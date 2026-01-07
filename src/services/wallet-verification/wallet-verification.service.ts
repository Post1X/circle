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
      this.logger.error(`Signature verification failed: ${error.message}`, {
        stack: error.stack,
        walletType,
        address,
        messageLength: message?.length,
        signatureLength: signature?.length,
      });
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

      if (!tronWeb.isAddress(address)) {
        this.logger.error(`Invalid TRON address: ${address}`);
        return false;
      }

      this.logger.log(`Verifying TRON signature - address: ${address}, message: ${message.substring(0, 50)}..., signature: ${signature.substring(0, 20)}...`);

      try {
        let cleanSignature = signature;
        if (signature.startsWith('0x')) {
          cleanSignature = signature.slice(2);
        }

        let verifyResult = tronWeb.trx.verifyMessageV2(message, cleanSignature);
        
        if (verifyResult && typeof verifyResult.then === 'function') {
          verifyResult = await verifyResult;
        }

        if (!verifyResult) {
          this.logger.warn(`TRON signature verification returned false`);
          return false;
        }

        const recoveredAddress = String(verifyResult).toLowerCase();
        const providedAddress = address.toLowerCase();

        const isValid = recoveredAddress === providedAddress;

        if (!isValid) {
          this.logger.warn(`TRON signature mismatch - provided: ${providedAddress}, recovered: ${recoveredAddress}`);
        }

        return isValid;
      } catch (innerError) {
        this.logger.error(`Error in TRON signature verification inner logic: ${innerError?.message || innerError}, type: ${typeof innerError}, stack: ${innerError?.stack}`);
        throw innerError;
      }
    } catch (error) {
      const errorMessage = error?.message || error?.toString() || String(error) || 'Unknown error';
      const errorStack = error?.stack || 'No stack trace';
      this.logger.error(`Tron signature verification error: ${errorMessage}`, {
        errorType: typeof error,
        errorConstructor: error?.constructor?.name,
        stack: errorStack,
        address,
        messageLength: message?.length,
        signatureLength: signature?.length,
        fullError: JSON.stringify(error, Object.getOwnPropertyNames(error)),
      });
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

