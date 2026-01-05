import { Module } from '@nestjs/common';
import { PublicController } from './public.controller';
import { AdminModule } from '../admin/admin.module';

@Module({
  imports: [AdminModule],
  controllers: [PublicController],
})
export class PublicModule {}

