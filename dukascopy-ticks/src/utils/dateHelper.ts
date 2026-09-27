import { injectable } from "inversify";

@injectable()
export class DateHelper {
  getDate(millis: number): Date {
    return new Date(millis);
  }

  convertToISOString(millis: number): string {
    return new Date(millis).toISOString();
  }
}