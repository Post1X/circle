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
} from '@nestjs/common';
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
} from './dto';
import * as crypto from 'crypto';

@Controller('api/users')
export class UsersController {
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

    await this.usersService.updateUsername(user.user_id, dto.username);
    return {
      success: true,
      username: dto.username,
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

  @Post('wallet-connect')
  async walletConnect(@Body() dto: WalletConnectDto) {
    const nonce = await this.usersService.getNonce(dto.address, dto.nonce);
    if (!nonce) {
      throw new UnauthorizedException('Invalid or expired nonce');
    }

    const isValid = await this.usersService.verifyWalletSignature(
      dto.wallet_type,
      dto.address,
      dto.message,
      dto.signature,
    );

    if (!isValid) {
      throw new UnauthorizedException('Invalid signature');
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

