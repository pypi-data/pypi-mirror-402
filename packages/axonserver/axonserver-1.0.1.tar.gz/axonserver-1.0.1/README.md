
# 🚀 How to Run AxonServer

Once you have installed the package via pip install axonserver, you can launch the OS Manager using any of the following methods:

1. The Direct Command (Recommended)
Because of our setup, you can launch the menu directly from your terminal or Cloud Shell without typing "python":

>> axonserver

2. Running as a Python Module
If the direct command isn't in your system path, use the module flag. This is the most reliable way to run it on Google Cloud Shell or GitHub Codespaces:

>> python3 -m axonserver

3. Inside a Python Script (The "Import" Way)
If you want to include AxonServer as part of your own project, you can import it like any other library:

>> import axonserver
>> axonserver.main()

4. The One-Liner (Quick Start)
To run it instantly without creating a file:

python3 -c "import axonserver; axonserver.main()"