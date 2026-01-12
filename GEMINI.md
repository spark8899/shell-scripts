# Shell Scripts & Utilities Repository

## Project Overview
This repository acts as a toolkit containing a diverse collection of shell and Python scripts for system administration, blockchain interaction, automation, monitoring, and application deployment. It is not a single monolithic application but rather a library of independent tools and mini-projects.

## Directory Structure

*   **`blockchain/`**: Python scripts for interacting with various blockchains (Ethereum, Tron, BSC, Solana, etc.). Includes tools for scanning balances (`scan_eth_usdt.py`) and transferring funds.
*   **`docker/`**: Utilities for managing Docker, such as cleaning logs and checking log sizes.
*   **`greatwall/`**: Scripts likely related to network configuration or proxy setups (`reality.sh`, `tcp-wss.sh`).
*   **`install/`**: System initialization scripts. `init_ubuntu.sh` configures a fresh Ubuntu server with standard settings (hostname, kernel optimizations, limits, essential packages).
*   **`locust/`**: Load testing scripts using the Locust framework (`locustfile.py`).
*   **`mysql/`**:
    *   General scripts for exporting data and querying user info.
    *   **`query01/`**: A FastAPI-based web application for data querying. Includes a `readme`, `requirements.txt`, and systemd service configuration.
    *   **`data_view/`**: Scripts for viewing data.
*   **`prometheus/`**: Monitoring scripts intended for use with Prometheus or similar systems (e.g., SSL expiry, domain expiry, application monitoring).
*   **`s3presigned/`**: Tools for generating S3 presigned URLs or handling S3 data.
*   **`script/`**: Miscellaneous automation scripts (backup, disk partitioning, Lark/Telegram forwarding).
*   **`telegram/`**: A collection of Telegram bots.
    *   **`checkin/`**: A bot for user check-ins, featuring database interaction and lottery logic.
    *   **`mybot/`**: A general-purpose bot including ChatGPT integration and crypto tools.
    *   **`tg-pusher/`**: A tool for pushing content to Telegram.
*   **`vm/`**: A robust suite of wrapper scripts (`create-vm`, `delete-vm`) around `virsh` and `cloud-init` for quickly creating and managing local KVM/QEMU virtual machines using cloud images.

## Key Components & Usage

### 1. VM Management (`vm/`)
*   **Purpose**: Automate the creation of local VMs for testing.
*   **Key Scripts**:
    *   `create-vm`: Creates a new VM from a cloud image (e.g., Ubuntu, CentOS).
    *   `delete-vm`: Destroys a VM.
    *   `get-vm-ip`: Retrieves the IP address of a running VM.
*   **Usage**:
    ```bash
    # Create a VM named "node1"
    ./create-vm -n node1 -i /path/to/image.img -k ~/.ssh/id_rsa.pub -s 20
    ```
*   **Prerequisites**: Requires `libvirt`, `virsh`, and `genisoimage` (or `cloud-localds`). See `vm/README.md` for detailed setup.

### 2. Telegram Bots (`telegram/`)
*   **Checkin Bot**: Located in `telegram/checkin/`.
    *   **Setup**: Requires a MySQL database. Initialize with `init_db.sql`.
    *   **Configuration**: create a `.env` file with `BOT_TOKEN`, `MYSQL_HOST`, etc.
    *   **Run**: `python3 main_bot.py`.
*   **Dependencies**: Typically requires `python-telegram-bot`, `mysql-connector-python`, `python-dotenv`.

### 3. Blockchain Scripts (`blockchain/`)
*   **Purpose**: Automate crypto asset scanning and transfers.
*   **Configuration**: Scripts often have variables for RPC endpoints (e.g., `rpc = "https://..."`) and contract addresses at the top of the file.
*   **Input**: Some scripts like `scan_eth_usdt.py` expect an `address.csv` file in the same directory.
*   **Dependencies**: `web3` (Python).

### 4. Web Application (`mysql/query01/`)
*   **Type**: FastAPI (Python).
*   **Running**:
    ```bash
    cd mysql/query01
    pip install -r requirements.txt
    uvicorn app:app --host 0.0.0.0 --port 8000
    ```
*   **Deployment**: A systemd unit file example is provided in the `readme`.

## Development Conventions

*   **Languages**: Primarily **Python** (3.x) and **Bash**.
*   **Environment**:
    *   Python scripts often imply a virtual environment or specific system packages.
    *   Secrets and configuration are frequently loaded from `.env` files (e.g., in `telegram/` and `mysql/query01/`) or hardcoded in headers (older/simpler scripts).
*   **Logging**:
    *   Python scripts often use the standard `logging` module or custom logging configurations (`logging.conf`).
    *   Bash scripts print directly to stdout/stderr.
*   **Databases**: MySQL is the primary database used for the persistent applications (Telegram bots, Web apps).

## Installation & Requirements

*   **System**: Linux/macOS (Bash scripts).
*   **Virtualization**: KVM/Libvirt is required for the `vm/` scripts.
*   **Python**: Python 3.x is required. It is recommended to use virtual environments (`venv`) for the Python projects to manage dependencies like `web3`, `fastapi`, `uvicorn`, `python-telegram-bot`.
