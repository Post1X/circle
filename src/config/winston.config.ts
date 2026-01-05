import { WinstonModuleOptions } from 'nest-winston';
import * as winston from 'winston';
import { AppConfigService } from './config.service';

const customFormat = winston.format.printf((info) => {
  const { timestamp, level, message, context } = info;
  const contextStr = context ? `[${context}]` : '';
  return `${timestamp} ${level} ${contextStr} ${message}`;
});

const consoleFormat = winston.format.combine(
  winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
  winston.format.colorize({ level: true }),
  winston.format.printf((info) => {
    const { timestamp, level, message, context } = info;
    const contextStr = context ? `\x1b[36m[${context}]\x1b[0m` : '';
    return `${timestamp} ${level} ${contextStr} ${message}`;
  }),
);

export const getWinstonConfig = (
  configService: AppConfigService,
): WinstonModuleOptions => {
  const isDevelopment = configService.mode === 'test';
  const logLevel = isDevelopment ? 'debug' : 'info';

  return {
    level: logLevel,
    format: winston.format.combine(
      winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
      winston.format.errors({ stack: true }),
      winston.format.splat(),
    ),
    transports: [
      new winston.transports.Console({
        format: consoleFormat,
      }),
      new winston.transports.File({
        filename: 'logs/error.log',
        level: 'error',
        format: winston.format.combine(
          winston.format.timestamp(),
          winston.format.json(),
        ),
        maxsize: 5242880,
        maxFiles: 5,
      }),
      new winston.transports.File({
        filename: 'logs/combined.log',
        format: winston.format.combine(
          winston.format.timestamp(),
          winston.format.json(),
        ),
        maxsize: 5242880,
        maxFiles: 5,
      }),
    ],
    exceptionHandlers: [
      new winston.transports.Console({
        format: consoleFormat,
      }),
      new winston.transports.File({
        filename: 'logs/exceptions.log',
        format: winston.format.combine(
          winston.format.timestamp(),
          winston.format.json(),
        ),
      }),
    ],
    rejectionHandlers: [
      new winston.transports.Console({
        format: consoleFormat,
      }),
      new winston.transports.File({
        filename: 'logs/rejections.log',
        format: winston.format.combine(
          winston.format.timestamp(),
          winston.format.json(),
        ),
      }),
    ],
  };
};

