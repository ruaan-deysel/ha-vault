import { css } from "lit";

export const themeTokens = css`
  :host {
    --vault-primary: var(--primary-color, #f59e0b);
    --vault-accent: #f59e0b;
    --vault-accent-light: #fbbf24;
    --vault-accent-muted: color-mix(in srgb, #f59e0b 16%, transparent);
    --vault-success: var(--success-color, #10b981);
    --vault-success-muted: color-mix(in srgb, #10b981 16%, transparent);
    --vault-warning: var(--warning-color, #f59e0b);
    --vault-warning-muted: color-mix(in srgb, #f59e0b 16%, transparent);
    --vault-error: var(--error-color, #ef4444);
    --vault-error-muted: color-mix(in srgb, #ef4444 16%, transparent);
    --vault-info: var(--info-color, #3b82f6);
    --vault-info-muted: color-mix(in srgb, #3b82f6 16%, transparent);
    --vault-standby: var(--disabled-text-color, #71717a);
    --vault-card-bg: var(--ha-card-background, var(--card-background-color, #18181b));
    --vault-surface: var(--secondary-background-color, rgba(255, 255, 255, 0.04));
    --vault-surface-hover: rgba(255, 255, 255, 0.08);
    --vault-border: var(--ha-card-border-color, var(--divider-color, rgba(255, 255, 255, 0.08)));
    --vault-radius: var(--ha-card-border-radius, 12px);
    --vault-text: var(--primary-text-color, #f4f4f5);
    --vault-subtext: var(--secondary-text-color, #a1a1aa);
  }
`;
