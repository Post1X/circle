import {
  Controller,
  Post,
  Get,
  Patch,
  Delete,
  Body,
  Param,
  UseGuards,
  HttpCode,
  HttpStatus,
  UnauthorizedException,
  HttpException,
  ParseIntPipe,
  Logger,
  UseInterceptors,
  UploadedFile,
  BadRequestException,
} from '@nestjs/common';
import { FileInterceptor } from '@nestjs/platform-express';
import { multerConfig } from '../../config/multer.config';
import { UsersService } from './users.service';
import { AuthService } from '../auth/auth.service';
import { JwtAuthGuard } from '../auth/guards/jwt-auth.guard';
import { CurrentUser } from '../auth/decorators/current-user.decorator';
import { User } from '../../entities/user.entity';
import { TokenService } from '../../services/token/token.service';
import {
  UserRegisterDto,
  UserLoginDto,
  UserLoginResponseDto,
  UpdateUsernameDto,
  WalletAuthDto,
  WalletConnectDto,
  WalletBindDto,
  WalletResponseDto,
  WalletType,
  BalanceResponseDto,
  TronAddressResponseDto,
  MagicLinkDto,
  MagicLinkResponseDto,
} from './dto';
import * as crypto from 'crypto';

@Controller('api/users')
export class UsersController {
  private readonly logger = new Logger(UsersController.name);

  constructor(
    private usersService: UsersService,
    private authService: AuthService,
    private tokenService: TokenService,
  ) {}

  @Post('register')
  async register(@Body() dto: UserRegisterDto) {
    await this.usersService.createUser(dto.username, dto.password);
    return { status: 'Registered successfully!' };
  }

  @Post('login')
  async login(@Body() dto: UserLoginDto): Promise<UserLoginResponseDto> {
    const user = await this.authService.validateUser(
      dto.username,
      dto.password,
    );

    if (!user) {
      throw new UnauthorizedException('Incorrect login or password');
    }

    const accessToken = await this.authService.createAccessToken(user.user_id);

    return {
      access_token: accessToken,
      user_id: user.user_id,
      username: user.username,
    };
  }

  @Post('logout')
  @UseGuards(JwtAuthGuard)
  @HttpCode(HttpStatus.OK)
  async logout(@CurrentUser() user: User) {
    return { message: 'Successfully logged out' };
  }

  @Get('me')
  @UseGuards(JwtAuthGuard)
  async getMe(@CurrentUser() user: User): Promise<User> {
    return user;
  }

  @Post('avatar')
  @UseGuards(JwtAuthGuard)
  @UseInterceptors(FileInterceptor('avatar', multerConfig))
  @HttpCode(HttpStatus.OK)
  async uploadAvatar(
    @CurrentUser() user: User,
    @UploadedFile() file: Express.Multer.File,
  ) {
    if (!file) {
      throw new BadRequestException('No file uploaded or invalid file type');
    }

    try {
      const avatarUrl = `/static/avatars/${file.filename}`;
      const updatedUser = await this.usersService.updateAvatarUrl(
        user.user_id,
        avatarUrl,
      );

      this.logger.log(`Avatar uploaded for user ${user.user_id}: ${avatarUrl}`);

      return {
        success: true,
        user: updatedUser,
        avatar_url: updatedUser.avatar_url,
        message: 'Avatar uploaded successfully',
      };
    } catch (error) {
      this.logger.error(`Failed to upload avatar for user ${user.user_id}: ${error.message}`);
      throw new BadRequestException('Failed to upload avatar');
    }
  }

  @Patch('username')
  @UseGuards(JwtAuthGuard)
  async updateUsername(
    @CurrentUser() user: User,
    @Body() dto: UpdateUsernameDto,
  ) {
    if (user.username === dto.username) {
      return {
        success: true,
        username: dto.username,
        message: 'Никнейм уже установлен',
      };
    }

    const existingUser = await this.usersService.getUserByUsername(
      dto.username,
    );
    if (existingUser && existingUser.user_id !== user.user_id) {
      return {
        success: false,
        error: 'Никнейм уже занят другим пользователем',
      };
    }

    const updatedUser = await this.usersService.updateUsername(user.user_id, dto.username);
    return {
      success: true,
      user: updatedUser,
      username: updatedUser.username,
      message: 'Никнейм успешно обновлен',
    };
  }

  @Get('balance')
  @UseGuards(JwtAuthGuard)
  async getBalance(@CurrentUser() user: User): Promise<BalanceResponseDto> {
    return {
      balance: parseFloat(user.balance.toString()),
      total_winnings: parseFloat(user.total_winnings.toString()),
      games_played: user.games_played,
    };
  }

  @Get('deposit/address')
  @UseGuards(JwtAuthGuard)
  async getDepositAddress(
    @CurrentUser() user: User,
  ): Promise<TronAddressResponseDto> {
    try {
      const address = await this.usersService.getDepositAddress(user.user_id);
      return {
        address,
        network: 'tron',
        message: 'Отправьте USDT на этот адрес для пополнения баланса',
      };
    } catch (error) {
      throw new HttpException(
        `Ошибка получения адреса: ${error.message}`,
        HttpStatus.INTERNAL_SERVER_ERROR,
      );
    }
  }

  @Post('nonce')
  async getNonce(@Body() dto: WalletAuthDto) {
    const nonce = await this.usersService.createNonce(dto.address);
    return { nonce };
  }
  // TODO: Add @Throttle(10, 60) decorator after installing @nestjs/throttler
  // This will limit to 10 requests per minute

  @Post('wallet-connect')
  async walletConnect(@Body() dto: WalletConnectDto) {
    this.logger.log(`Wallet connect request - address: ${dto.address}, nonce: ${dto.nonce}, nonceLength: ${dto.nonce?.length}, walletType: ${dto.wallet_type}`);

    const nonce = await this.usersService.getNonce(dto.address, dto.nonce);
    if (!nonce) {
      this.logger.warn(`Nonce not found, checking status - address: ${dto.address}, nonce: ${dto.nonce.substring(0, 16)}...`);

      const usedNonce = await this.usersService.checkNonceStatus(
        dto.address,
        dto.nonce,
      );
      
      this.logger.warn(`Nonce status check result - address: ${dto.address}, status: ${usedNonce}`);

      if (usedNonce === 'used') {
        throw new UnauthorizedException('Nonce has already been used');
      }
      if (usedNonce === 'expired') {
        throw new UnauthorizedException(
          'Nonce has expired. Please request a new one.',
        );
      }
      throw new UnauthorizedException('Invalid or expired nonce');
    }

    const isValid = await this.usersService.verifyWalletSignature(
      dto.wallet_type,
      dto.address,
      dto.message,
      dto.signature,
    );

    if (!isValid) {
      throw new UnauthorizedException('Signature verification failed');
    }

    await this.usersService.markNonceAsUsed(nonce);

    let user = await this.usersService.getUserByWalletAddress(dto.address);

    if (!user) {
      const randomUsername = `user_${Math.random().toString(36).substring(7)}`;
      user = await this.usersService.createUser(
        randomUsername,
        crypto.randomBytes(16).toString('hex'),
      );
      await this.usersService.bindWalletToUser(
        user.user_id,
        dto.address,
        dto.wallet_type,
        false,
      );
    }

    const accessToken = await this.authService.createAccessToken(user.user_id);

    return {
      success: true,
      message: 'Wallet connected successfully',
      wallet_address: dto.address,
      wallet_type: dto.wallet_type,
      access_token: accessToken,
      user_id: user.user_id,
      username: user.username,
      balance: parseFloat(user.balance.toString()),
      games_played: user.games_played,
      total_winnings: parseFloat(user.total_winnings.toString()),
      leaderboard_rank: user.leaderboard_rank,
      is_admin: user.is_admin,
      avatar_url: user.avatar_url,
    };
  }

  @Post('magic-link')
  async magicLink(@Body() dto: MagicLinkDto): Promise<MagicLinkResponseDto> {
    const { user, accessToken } = await this.usersService.connectMagicLink(
      dto.address,
      dto.did_token,
    );

    return {
      access_token: accessToken,
      user_id: user.user_id,
      wallet_address: dto.address,
      username: user.username,
    };
  }

  @Post('wallet/bind')
  @UseGuards(JwtAuthGuard)
  async bindWallet(
    @CurrentUser() user: User,
    @Body() dto: WalletBindDto,
  ): Promise<WalletResponseDto> {
    const wallet = await this.usersService.bindWalletToUser(
      user.user_id,
      dto.address,
      dto.wallet_type,
      true,
      dto.message,
      dto.signature,
    );

    return {
      id: wallet.id,
      address: wallet.address,
      network: wallet.network,
      wallet_type: dto.wallet_type,
      is_primary: wallet.is_primary,
      created_at: wallet.created_at,
    };
  }

  @Get('wallets')
  @UseGuards(JwtAuthGuard)
  async getWallets(@CurrentUser() user: User): Promise<WalletResponseDto[]> {
    const wallets = await this.usersService.getUserWallets(user.user_id);
    return wallets.map((w) => ({
      id: w.id,
      address: w.address,
      network: w.network,
      wallet_type: (w.wallet_type as WalletType) || WalletType.TRONLINK,
      is_primary: w.is_primary,
      created_at: w.created_at,
    }));
  }

  @Post('wallet/:id/primary')
  @UseGuards(JwtAuthGuard)
  async setPrimaryWallet(
    @CurrentUser() user: User,
    @Param('id', ParseIntPipe) walletId: number,
  ): Promise<WalletResponseDto> {
    const wallet = await this.usersService.setPrimaryWallet(
      user.user_id,
      walletId,
    );
    return {
      id: wallet.id,
      address: wallet.address,
      network: wallet.network,
      wallet_type: (wallet.wallet_type as WalletType) || WalletType.TRONLINK,
      is_primary: wallet.is_primary,
      created_at: wallet.created_at,
    };
  }

  @Delete('wallet/:id')
  @UseGuards(JwtAuthGuard)
  @HttpCode(HttpStatus.OK)
  async unbindWallet(
    @CurrentUser() user: User,
    @Param('id', ParseIntPipe) walletId: number,
  ) {
    await this.usersService.unbindWallet(user.user_id, walletId);
    return { message: 'Wallet unbound successfully' };
  }
}

