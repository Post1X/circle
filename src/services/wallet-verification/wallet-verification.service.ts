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

        this.logger.debug(`Original message: "${message}"`);
        this.logger.debug(`Message length: ${message.length}`);

        let verifyResult;
        let triedMethods = [];

        const methods = [
          {
            name: 'verifyMessageV2 with string (no prefix)',
            fn: () => tronWeb.trx.verifyMessageV2 ? tronWeb.trx.verifyMessageV2(message, cleanSignature) : null,
          },
          {
            name: 'verifyMessage with string (no prefix)',
            fn: () => tronWeb.trx.verifyMessage(message, cleanSignature),
          },
          {
            name: 'verifyMessageV2 with hex (no prefix)',
            fn: () => {
              const messageHex = Buffer.from(message).toString('hex');
              return tronWeb.trx.verifyMessageV2 ? tronWeb.trx.verifyMessageV2(messageHex, cleanSignature) : null;
            },
          },
          {
            name: 'verifyMessage with hex (no prefix)',
            fn: () => {
              const messageHex = Buffer.from(message).toString('hex');
              return tronWeb.trx.verifyMessage(messageHex, cleanSignature);
            },
          },
          {
            name: 'verifyMessageV2 with string (with prefix)',
            fn: () => {
              const messageWithPrefix = `TRON Signed Message:\n${message}`;
              return tronWeb.trx.verifyMessageV2 ? tronWeb.trx.verifyMessageV2(messageWithPrefix, cleanSignature) : null;
            },
          },
          {
            name: 'verifyMessage with string (with prefix)',
            fn: () => {
              const messageWithPrefix = `TRON Signed Message:\n${message}`;
              return tronWeb.trx.verifyMessage(messageWithPrefix, cleanSignature);
            },
          },
          {
            name: 'verifyMessageV2 with hex (with prefix)',
            fn: () => {
              const messageWithPrefix = `TRON Signed Message:\n${message}`;
              const messageHex = Buffer.from(messageWithPrefix).toString('hex');
              return tronWeb.trx.verifyMessageV2 ? tronWeb.trx.verifyMessageV2(messageHex, cleanSignature) : null;
            },
          },
          {
            name: 'verifyMessage with hex (with prefix)',
            fn: () => {
              const messageWithPrefix = `TRON Signed Message:\n${message}`;
              const messageHex = Buffer.from(messageWithPrefix).toString('hex');
              return tronWeb.trx.verifyMessage(messageHex, cleanSignature);
            },
          },
        ];

        for (const method of methods) {
          if (!method.fn) continue;
          
          try {
            this.logger.debug(`Trying: ${method.name}`);
            const result = method.fn();
            
            if (result && typeof result.then === 'function') {
              verifyResult = await result;
            } else {
              verifyResult = result;
            }

            if (verifyResult) {
              this.logger.log(`SUCCESS with method: ${method.name}, recovered address: ${verifyResult}`);
              triedMethods.push(`${method.name}: SUCCESS (${verifyResult})`);
              break;
            } else {
              triedMethods.push(`${method.name}: returned false/null`);
            }
          } catch (error) {
            const errorMsg = typeof error === 'string' ? error : (error?.message || String(error));
            triedMethods.push(`${method.name}: ERROR (${errorMsg})`);
            this.logger.debug(`${method.name} failed: ${errorMsg}`);
            continue;
          }
        }

        if (triedMethods.length > 0) {
          this.logger.debug(`All tried methods: ${triedMethods.join(' | ')}`);
        }

        if (!verifyResult) {
          this.logger.warn(`TRON signature verification returned false - address: ${address}, messageLength: ${message.length}, signatureLength: ${signature.length}`);
          return false;
        }

        this.logger.debug(`Processing recoveredAddress from verifyResult: ${verifyResult}`);
        let recoveredAddress = verifyResult;
        if (recoveredAddress && typeof recoveredAddress.then === 'function') {
          this.logger.debug(`recoveredAddress is Promise, awaiting...`);
          recoveredAddress = await recoveredAddress;
          this.logger.debug(`Promise resolved to: ${recoveredAddress}`);
        }
        recoveredAddress = String(recoveredAddress);
        this.logger.debug(`recoveredAddress (final): ${recoveredAddress}`);

        const providedAddress = address;
        this.logger.debug(`Provided address: ${providedAddress}`);

        const recoveredAddressLower = recoveredAddress.toLowerCase();
        const providedAddressLower = providedAddress.toLowerCase();

        this.logger.log(`TRON address comparison (base58) - provided: ${providedAddressLower}, recovered: ${recoveredAddressLower}`);

        let isValid = recoveredAddressLower === providedAddressLower;

        if (!isValid) {
          this.logger.debug(`Base58 comparison failed, trying hex comparison...`);
          let recoveredAddressHex = tronWeb.address.toHex(recoveredAddress);
          if (recoveredAddressHex && typeof recoveredAddressHex.then === 'function') {
            recoveredAddressHex = await recoveredAddressHex;
          }
          recoveredAddressHex = String(recoveredAddressHex).toLowerCase();

          let providedAddressHex = tronWeb.address.toHex(providedAddress);
          if (providedAddressHex && typeof providedAddressHex.then === 'function') {
            providedAddressHex = await providedAddressHex;
          }
          providedAddressHex = String(providedAddressHex).toLowerCase();

          this.logger.log(`TRON address comparison (hex) - provided: ${providedAddressHex}, recovered: ${recoveredAddressHex}`);
          isValid = recoveredAddressHex === providedAddressHex;
        }

        if (!isValid) {
          this.logger.warn(`TRON signature mismatch - provided: ${providedAddressLower}, recovered: ${recoveredAddressLower}`);
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

