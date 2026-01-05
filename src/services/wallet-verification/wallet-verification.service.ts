import { Injectable, Logger, BadRequestException } from '@nestjs/common';
import { WalletType, BlockchainNetwork } from '../../modules/users/dto/wallet.dto';

@Injectable()
export class WalletVerificationService {
  private readonly logger = new Logger(WalletVerificationService.name);

  getNetworkFromWalletType(walletType: WalletType): BlockchainNetwork {
    switch (walletType) {
      case WalletType.TRONLINK:
      case WalletType.SAFEPAL:
        return BlockchainNetwork.TRON;
      case WalletType.SOLFLARE:
      case WalletType.PHANTOM:
      case WalletType.SOLONG:
        return BlockchainNetwork.SOLANA;
      case WalletType.METAMASK:
      case WalletType.LEDGER:
      case WalletType.TORUS:
        return BlockchainNetwork.ETHEREUM;
      default:
        throw new BadRequestException(`Unknown wallet type: ${walletType}`);
    }
  }

  async verifySignature(
    walletType: WalletType,
    address: string,
    message: string,
    signature: string,
  ): Promise<boolean> {
    const network = this.getNetworkFromWalletType(walletType);

    try {
      switch (network) {
        case BlockchainNetwork.TRON:
          return await this.verifyTronSignature(address, message, signature);
        case BlockchainNetwork.SOLANA:
          return await this.verifySolanaSignature(address, message, signature);
        case BlockchainNetwork.ETHEREUM:
        case BlockchainNetwork.BSC:
        case BlockchainNetwork.POLYGON:
          return await this.verifyEthereumSignature(address, message, signature);
        default:
          throw new BadRequestException(`Unsupported network: ${network}`);
      }
    } catch (error) {
      this.logger.error(`Signature verification failed: ${error.message}`);
      return false;
    }
  }

  private async verifyTronSignature(
    address: string,
    message: string,
    signature: string,
  ): Promise<boolean> {
    try {
      const TronWeb = require('tronweb');
      const tronWeb = new TronWeb({
        fullHost: 'https://api.trongrid.io',
      });

      const messageHex = Buffer.from(message).toString('hex');
      const recoveredAddress = tronWeb.address.fromHex(
        tronWeb.trx.verifyMessage(messageHex, signature),
      );

      return (
        tronWeb.address.toHex(address).toLowerCase() ===
        tronWeb.address.toHex(recoveredAddress).toLowerCase()
      );
    } catch (error) {
      this.logger.error(`Tron signature verification error: ${error.message}`);
      return false;
    }
  }

  private async verifySolanaSignature(
    address: string,
    message: string,
    signature: string,
  ): Promise<boolean> {
    try {
      const nacl = require('tweetnacl');
      const bs58 = require('bs58');

      const messageBytes = new TextEncoder().encode(message);
      const signatureBytes = bs58.decode(signature);
      const publicKeyBytes = bs58.decode(address);

      return nacl.sign.detached.verify(messageBytes, signatureBytes, publicKeyBytes);
    } catch (error) {
      this.logger.error(`Solana signature verification error: ${error.message}`);
      return false;
    }
  }

  private async verifyEthereumSignature(
    address: string,
    message: string,
    signature: string,
  ): Promise<boolean> {
    try {
      const { ethers } = require('ethers');

      const messageHash = ethers.hashMessage(message);
      const recoveredAddress = ethers.recoverAddress(messageHash, signature);

      return recoveredAddress.toLowerCase() === address.toLowerCase();
    } catch (error) {
      this.logger.error(`Ethereum signature verification error: ${error.message}`);
      return false;
    }
  }

  validateAddress(address: string, network: BlockchainNetwork): boolean {
    try {
      switch (network) {
        case BlockchainNetwork.TRON:
          const TronWeb = require('tronweb');
          return TronWeb.isAddress(address);
        case BlockchainNetwork.SOLANA:
          const bs58 = require('bs58');
          try {
            bs58.decode(address);
            return address.length >= 32 && address.length <= 44;
          } catch {
            return false;
          }
        case BlockchainNetwork.ETHEREUM:
        case BlockchainNetwork.BSC:
        case BlockchainNetwork.POLYGON:
          const { ethers } = require('ethers');
          return ethers.isAddress(address);
        default:
          return false;
      }
    } catch (error) {
      return false;
    }
  }
}

