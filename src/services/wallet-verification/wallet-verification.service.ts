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
          this.logger.debug(`Removed 0x prefix from signature: ${cleanSignature.substring(0, 20)}...`);
        }

        const messageHex = Buffer.from(message).toString('hex');
        this.logger.debug(`Message converted to hex: ${messageHex.substring(0, 50)}... (length: ${messageHex.length})`);

        this.logger.debug(`Calling verifyMessage with hex message and signature`);
        let verifyResult;
        try {
          verifyResult = tronWeb.trx.verifyMessage(messageHex, cleanSignature);
          this.logger.debug(`verifyMessage returned, type: ${typeof verifyResult}, value: ${verifyResult}`);
        } catch (verifyError) {
          const errorMsg = typeof verifyError === 'string' ? verifyError : (verifyError?.message || String(verifyError));
          this.logger.error(`verifyMessage threw error: ${errorMsg}, stack: ${verifyError?.stack}`);
          throw verifyError;
        }

        if (!verifyResult) {
          this.logger.warn(`TRON signature verification returned false - address: ${address}, messageLength: ${message.length}, signatureLength: ${signature.length}`);
          return false;
        }

        this.logger.debug(`Processing recoveredAddressHex from verifyResult: ${verifyResult}`);
        let recoveredAddressHex = verifyResult;
        if (recoveredAddressHex && typeof recoveredAddressHex.then === 'function') {
          this.logger.debug(`recoveredAddressHex is Promise, awaiting...`);
          recoveredAddressHex = await recoveredAddressHex;
          this.logger.debug(`Promise resolved to: ${recoveredAddressHex}`);
        }
        recoveredAddressHex = String(recoveredAddressHex).toLowerCase();
        this.logger.debug(`recoveredAddressHex (final): ${recoveredAddressHex}`);

        this.logger.debug(`Calling toHex for provided address: ${address}`);
        let providedAddressHex;
        try {
          providedAddressHex = tronWeb.address.toHex(address);
          this.logger.debug(`toHex returned, type: ${typeof providedAddressHex}, value: ${providedAddressHex}`);
        } catch (toHexError) {
          this.logger.error(`toHex threw error: ${toHexError?.message || toHexError}, stack: ${toHexError?.stack}`);
          throw toHexError;
        }

        if (providedAddressHex && typeof providedAddressHex.then === 'function') {
          this.logger.debug(`providedAddressHex is Promise, awaiting...`);
          providedAddressHex = await providedAddressHex;
          this.logger.debug(`Promise resolved to: ${providedAddressHex}`);
        }
        providedAddressHex = String(providedAddressHex).toLowerCase();
        this.logger.debug(`providedAddressHex (final): ${providedAddressHex}`);

        this.logger.log(`TRON address comparison (hex) - provided: ${providedAddressHex}, recovered: ${recoveredAddressHex}`);

        const isValid = recoveredAddressHex === providedAddressHex;

        if (!isValid) {
          this.logger.warn(`TRON signature mismatch - provided: ${address} (hex: ${providedAddressHex}), recovered hex: ${recoveredAddressHex}`);
        } else {
          this.logger.log(`TRON signature verified successfully - address: ${address}`);
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

