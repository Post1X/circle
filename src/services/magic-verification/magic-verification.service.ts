import { Injectable, Logger, UnauthorizedException } from '@nestjs/common';
import { AppConfigService } from '../../config/config.service';
import axios from 'axios';

@Injectable()
export class MagicVerificationService {
  private readonly logger = new Logger(MagicVerificationService.name);
  private readonly magicApiUrl = 'https://api.magic.link';

  constructor(private configService: AppConfigService) {}

  async verifyDidToken(didToken: string): Promise<{
    issuer: string;
    publicAddress: string;
    email?: string;
  }> {
    const secretKey = this.configService.magicSecretKey;

    if (!secretKey) {
      throw new Error('MAGIC_SECRET_KEY is not configured');
    }

    try {
      let MagicAdmin: any;
      try {
        MagicAdmin = require('@magic-sdk/admin');
        const magic = new MagicAdmin.MagicAdmin(secretKey);
        const metadata = await magic.users.getMetadataByToken(didToken);

        return {
          issuer: metadata.issuer || '',
          publicAddress: metadata.publicAddress || '',
          email: metadata.email || undefined,
        };
      } catch (libError) {
        this.logger.warn('@magic-sdk/admin not available, using direct API call');
        return await this.verifyDidTokenViaAPI(didToken, secretKey);
      }
    } catch (error) {
      if (error.response) {
        this.logger.error(
          `Magic API error: ${error.response.status} - ${JSON.stringify(error.response.data)}`,
        );
        this.logger.error(`Request URL: ${this.magicApiUrl}/v1/admin/auth/user/get`);
        this.logger.error(`Secret Key present: ${!!secretKey}`);
      } else {
        this.logger.error(`Magic DID token verification failed: ${error.message}`);
        if (error.stack) {
          this.logger.error(`Error stack: ${error.stack}`);
        }
      }

      if (error.response) {
        if (error.response.status === 401 || error.response.status === 403) {
          throw new UnauthorizedException('Invalid or expired DID token');
        }
        if (error.response.status === 400) {
          throw new UnauthorizedException(
            `Invalid DID token format: ${error.response.data?.message || ''}`,
          );
        }
        throw new UnauthorizedException(
          `Failed to verify DID token with Magic: ${error.response.data?.message || error.response.statusText}`,
        );
      }

      throw new UnauthorizedException(`Failed to verify DID token: ${error.message}`);
    }
  }

  private async verifyDidTokenViaAPI(
    didToken: string,
    secretKey: string,
  ): Promise<{
    issuer: string;
    publicAddress: string;
    email?: string;
  }> {
    try {
      const decodedToken = Buffer.from(didToken, 'base64').toString('utf-8');
      const tokenParts = JSON.parse(decodedToken);
      
      if (!Array.isArray(tokenParts) || tokenParts.length < 2) {
        throw new UnauthorizedException('Invalid DID token format');
      }

      const claims = JSON.parse(tokenParts[1]);
      const issuer = claims.iss || claims.issuer;

      if (!issuer) {
        throw new UnauthorizedException('Issuer not found in DID token');
      }

      const response = await axios.get(
        `${this.magicApiUrl}/v1/admin/auth/user/get`,
        {
          params: {
            did_token: didToken,
            issuer: issuer,
          },
          headers: {
            'X-Magic-Secret-Key': secretKey,
            'Content-Type': 'application/json',
          },
        },
      );

      if (!response.data || !response.data.data) {
        throw new UnauthorizedException('Invalid DID token');
      }

      const userData = response.data.data;

      return {
        issuer: userData.issuer || '',
        publicAddress: userData.public_address || userData.publicAddress || '',
        email: userData.email || undefined,
      };
    } catch (error) {
      if (error.response) {
        this.logger.error(
          `Magic API direct call error: ${error.response.status} - ${JSON.stringify(error.response.data)}`,
        );
        this.logger.error(`Request URL: ${this.magicApiUrl}/v1/admin/auth/user/get`);
      } else {
        this.logger.error(`Magic API direct call failed: ${error.message}`);
      }

      throw error;
    }
  }

  validateAddress(address: string): boolean {
    return /^0x[a-fA-F0-9]{40}$/.test(address);
  }
}
