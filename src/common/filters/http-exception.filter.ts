import {
  ExceptionFilter,
  Catch,
  ArgumentsHost,
  HttpException,
  HttpStatus,
  LoggerService,
} from '@nestjs/common';
import { Request, Response } from 'express';

@Catch()
export class HttpExceptionFilter implements ExceptionFilter {
  constructor(private readonly logger: LoggerService) {}

  catch(exception: unknown, host: ArgumentsHost) {
    const ctx = host.switchToHttp();
    const response = ctx.getResponse<Response>();
    const request = ctx.getRequest<Request>();

    const status =
      exception instanceof HttpException
        ? exception.getStatus()
        : HttpStatus.INTERNAL_SERVER_ERROR;

    const message =
      exception instanceof HttpException
        ? exception.getResponse()
        : 'Internal server error';

    const errorResponse = {
      statusCode: status,
      timestamp: new Date().toISOString(),
      path: request.url,
      method: request.method,
      message:
        typeof message === 'string'
          ? message
          : (message as any)?.message || 'Internal server error',
    };

    const errorMessage =
      exception instanceof Error
        ? exception.message
        : typeof exception === 'string'
          ? exception
          : 'Unknown error';

    const logMessage = `${request.method} ${request.url} ${status} - ${errorMessage}`;

    if (status >= 500) {
      this.logger.error(logMessage, 'ExceptionFilter');
    } else {
      this.logger.warn(logMessage, 'ExceptionFilter');
    }

    response.status(status).json(errorResponse);
  }
}

