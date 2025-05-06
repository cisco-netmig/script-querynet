import logging

logger = logging.getLogger(__name__)

import os
from PyQt5.QtCore import QThread, pyqtSignal
from concurrent.futures import ThreadPoolExecutor
from time import sleep

from .azureai_client import AzureAIClient


class QueryThread(QThread):
    """
    Worker thread to handle running commands on network devices and querying Azure AI for answers.
    Emits results via signals.
    """
    result_ready = pyqtSignal(str)
    add_progress = pyqtSignal(float)

    def __init__(self, form, devices, query):
        """
        Initializes the query thread with form, devices, and user query.
        """
        super().__init__()
        self.form = form
        self.devices = devices
        self.query = query
        self.output_data = {}

    def run(self):
        """
        Executes commands on devices and queries Azure AI for answers.
        """
        self.azure_ai = AzureAIClient(os.path.join(os.path.expanduser('~'), '.netmig', 'querynet.env'))

        # Step 1: Run commands on devices using thread pool
        self.thread_executor()

        # Step 2: Ask for answers from Azure AI
        answer_prompt = (
            "The following is the CLI output from multiple network devices. "
            "For each device, analyze the output and answer the user's question clearly and concisely. "
            "Group the answers per device. If the data lends itself to structured comparison, return the result in a table format. "
            "Otherwise, use a clean and readable text layout. Do not include the commands or repeat the question.\n\n"
            f"User Question: {self.query}\n\nCLI Outputs:\n{{}}"
        )

        full_output = ""
        for device, command_outputs in self.output_data.items():
            full_output += f"=== Device: {device} ===\n"
            for cmd, out in command_outputs.items():
                full_output += f"{cmd}\n{out}\n"
            full_output += "\n"

        html_answer = self.azure_ai.ask(answer_prompt.format(full_output), self.query, "html")
        self.result_ready.emit(html_answer)

    def thread_executor(self):
        """
        Executes the command runner for each device using a thread pool executor.
        """
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = {
                device: executor.submit(self.command_runner, device)
                for device in self.devices
            }
            sleep(0.5)
            executor.shutdown(wait=True)

            for device, future in futures.items():
                exception = future.exception()
                if exception:
                    logger.error("Exception for %s: %s", device, exception)

    def command_runner(self, device):
        """
        Connects to a device, runs commands, and stores the output.
        """
        from netcore import GenericHandler

        self.output_data[device] = {}

        logger.info("Connecting to %s...", device)
        proxy = None
        if self.form.session.get("JUMPHOST_IP"):
            proxy = {
                "hostname": self.form.session["JUMPHOST_IP"],
                "username": self.form.session["JUMPHOST_USERNAME"],
                "password": self.form.session["JUMPHOST_PASSWORD"],
            }

        handler = GenericHandler(
            hostname=device,
            username=self.form.session["NETWORK_USERNAME"],
            password=self.form.session["NETWORK_PASSWORD"],
            proxy=proxy,
            handler="NETMIKO"
        )

        device_type = handler.device_type
        logger.info(f"Connected to {device}")

        # Ask AzureAI for the commands with device type context
        command_prompt = (
            f"You are a network automation assistant. "
            f"The target device is a {device_type}. "
            f"The user's query may require multiple CLI show commands. "
            f"Return all necessary commands as a comma-separated list, with no explanations or extra text. "
            f"Each command should be compatible with the given device type."
        )

        command_list = self.azure_ai.ask(command_prompt, self.query, "plain").strip().split(",")

        for cmd in command_list:
            output = handler.send_command(cmd).strip()
            self.output_data[device][cmd] = output

        handler.close()
