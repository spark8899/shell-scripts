# pip3 install solders solana

from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.system_program import TransferParams, transfer

from solana.transaction import Transaction

import asyncio
from solana.rpc.async_api import AsyncClient

async def transfer_sol(sender: Keypair, recipient: Pubkey, amount: int):
    # Connect to the Solana devnet
    async with AsyncClient("https://api.devnet.solana.com") as client:
        # Create a transaction
        transaction = Transaction().add(transfer(TransferParams(from_pubkey=sender.pubkey(), to_pubkey=recipient, lamports=amount)))

        # Send the transaction
        tx_hash = await client.send_transaction(transaction, sender)

        # Wait for confirmation
        await client.confirm_transaction(tx_hash.value)

        print(f"Transaction completed. Hash: {tx_hash.value}")


# Main execution
if __name__ == "__main__":
    # Replace with your actual sender's private key
    sender_private_key = 'YourBase58Key'
    sender = Keypair.from_base58_string(sender_private_key)

    # Replace with the recipient's address
    recipient = Pubkey.from_string("RecipientPublicKeyHere")

    # Amount to transfer in lamports (1 SOL = 1,000,000,000 lamports)
    amount = 1 * 10**9  # Sending 1 SOL

    # Run the transfer
    asyncio.run(transfer_sol(sender, recipient, amount))
