import { css } from "lit";
import { themeTokens } from "./styles";

export const dashboardCardStyles = [
  themeTokens,
  css`
    :host {
      display: block;
      height: 100%;
      box-sizing: border-box;
    }

    ha-card {
      height: 100%;
      box-sizing: border-box;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 12px;
      overflow: hidden;
      background: var(--vault-card-bg);
      border: 1px solid var(--vault-border);
      border-radius: var(--vault-radius);
      color: var(--vault-text);
      font-family: var(--ha-card-font-family, inherit);
    }

    :host([embedded]) ha-card {
      border: none;
      box-shadow: none;
      background: transparent;
      padding: 0;
    }

    .icon {
      display: inline-block;
      vertical-align: middle;
      fill: currentColor;
      flex-shrink: 0;
    }

    /* Card Header */
    .header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
    }

    .header-main {
      display: flex;
      align-items: center;
      gap: 10px;
      min-width: 0;
    }

    .header-icon {
      width: 32px;
      height: 32px;
      border-radius: 8px;
      background: var(--vault-accent-muted);
      color: var(--vault-accent);
      display: grid;
      place-items: center;
      flex-shrink: 0;
    }

    .header-icon.success {
      background: var(--vault-success-muted);
      color: var(--vault-success);
    }

    .header-icon.error {
      background: var(--vault-error-muted);
      color: var(--vault-error);
    }

    .header-titles {
      display: flex;
      flex-direction: column;
      min-width: 0;
    }

    .header-tag {
      font-size: 0.72rem;
      font-weight: 700;
      letter-spacing: 0.05em;
      text-transform: uppercase;
      color: var(--vault-subtext);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .header-title {
      font-size: 1.05rem;
      font-weight: 700;
      color: var(--vault-text);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      line-height: 1.25;
    }

    .header-subtitle {
      font-size: 0.75rem;
      color: var(--vault-subtext);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .header-actions {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-shrink: 0;
    }

    /* KPI Display (Health, Protected, Next run, Last backup) */
    .kpi-container {
      display: flex;
      align-items: center;
      gap: 16px;
      padding-top: 4px;
    }

    .kpi-main {
      display: flex;
      flex-direction: column;
      min-width: 0;
    }

    .kpi-value-row {
      display: flex;
      align-items: baseline;
      gap: 4px;
    }

    .kpi-value {
      font-size: 1.85rem;
      font-weight: 800;
      line-height: 1.1;
      color: var(--vault-text);
      letter-spacing: -0.02em;
    }

    .kpi-unit {
      font-size: 1rem;
      font-weight: 600;
      color: var(--vault-subtext);
    }

    .kpi-label {
      font-size: 0.82rem;
      font-weight: 600;
      color: var(--vault-text);
      margin-top: 2px;
    }

    .kpi-sub {
      font-size: 0.75rem;
      color: var(--vault-subtext);
      margin-top: 2px;
    }

    /* Circular Score Gauge */
    .score-circle {
      position: relative;
      width: 52px;
      height: 52px;
      flex-shrink: 0;
      display: grid;
      place-items: center;
    }

    .score-circle svg {
      width: 100%;
      height: 100%;
      transform: rotate(-90deg);
    }

    .score-circle circle {
      fill: none;
      stroke-width: 5;
    }

    .score-circle-bg {
      stroke: rgba(255, 255, 255, 0.08);
    }

    .score-circle-fill {
      stroke: var(--vault-success);
      stroke-linecap: round;
      transition: stroke-dashoffset 0.5s ease;
    }

    .score-text {
      position: absolute;
      font-size: 0.85rem;
      font-weight: 800;
      color: var(--vault-text);
    }

    /* Status Badges */
    .badge {
      display: inline-flex;
      align-items: center;
      gap: 5px;
      font-size: 0.72rem;
      font-weight: 600;
      padding: 3px 8px;
      border-radius: 9999px;
      line-height: 1.2;
      width: fit-content;
    }

    .badge-dot {
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: currentColor;
    }

    .badge.success {
      background: var(--vault-success-muted);
      color: var(--vault-success);
    }

    .badge.running {
      background: var(--vault-info-muted);
      color: var(--vault-info);
    }

    .badge.warning {
      background: var(--vault-warning-muted);
      color: var(--vault-warning);
    }

    .badge.error {
      background: var(--vault-error-muted);
      color: var(--vault-error);
    }

    .badge.neutral {
      background: rgba(255, 255, 255, 0.06);
      color: var(--vault-subtext);
    }

    /* Progress bar */
    .progress-bar {
      width: 100%;
      height: 6px;
      background: rgba(255, 255, 255, 0.08);
      border-radius: 9999px;
      overflow: hidden;
      position: relative;
    }

    .progress-fill {
      height: 100%;
      background: var(--vault-success);
      border-radius: 9999px;
      transition: width 0.3s ease;
    }

    .progress-fill.running {
      background: var(--vault-info);
      background-image: linear-gradient(
        45deg,
        rgba(255, 255, 255, 0.15) 25%,
        transparent 25%,
        transparent 50%,
        rgba(255, 255, 255, 0.15) 50%,
        rgba(255, 255, 255, 0.15) 75%,
        transparent 75%,
        transparent
      );
      background-size: 16px 16px;
      animation: progress-stripes 1s linear infinite;
    }

    .progress-fill.warning {
      background: var(--vault-warning);
    }

    .progress-fill.error {
      background: var(--vault-error);
    }

    @keyframes progress-stripes {
      from {
        background-position: 16px 0;
      }
      to {
        background-position: 0 0;
      }
    }

    /* List items & Job Rows */
    .item-list {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }

    .card-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding: 10px 12px;
      background: var(--vault-surface);
      border: 1px solid var(--vault-border);
      border-radius: 8px;
      transition: background 0.15s ease, border-color 0.15s ease;
    }

    .card-row:hover {
      background: var(--vault-surface-hover);
    }

    .card-row-main {
      display: flex;
      flex-direction: column;
      gap: 3px;
      min-width: 0;
      flex: 1;
    }

    .card-row-title-bar {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
    }

    .card-row-title {
      font-size: 0.88rem;
      font-weight: 600;
      color: var(--vault-text);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .card-row-meta {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 0.75rem;
      color: var(--vault-subtext);
      flex-wrap: wrap;
    }

    .card-row-actions {
      display: flex;
      align-items: center;
      gap: 6px;
      flex-shrink: 0;
    }

    /* Action Buttons */
    .btn {
      display: inline-flex;
      align-items: center;
      gap: 5px;
      padding: 5px 10px;
      border-radius: 6px;
      font-size: 0.75rem;
      font-weight: 600;
      cursor: pointer;
      border: 1px solid transparent;
      transition: all 0.15s ease;
      background: rgba(255, 255, 255, 0.08);
      color: var(--vault-text);
    }

    .btn:hover:not(:disabled) {
      background: rgba(255, 255, 255, 0.14);
    }

    .btn:disabled {
      opacity: 0.4;
      cursor: not-allowed;
    }

    .btn.primary {
      background: var(--vault-accent);
      color: #111116;
      border-color: var(--vault-accent);
    }

    .btn.primary:hover:not(:disabled) {
      background: var(--vault-accent-light);
      border-color: var(--vault-accent-light);
    }

    .btn.amber {
      background: color-mix(in srgb, #f59e0b 20%, transparent);
      color: var(--vault-accent);
      border-color: color-mix(in srgb, #f59e0b 30%, transparent);
    }

    .btn.amber:hover:not(:disabled) {
      background: color-mix(in srgb, #f59e0b 30%, transparent);
    }

    /* Tag Chips (Items in backup, e.g. ✓ plex, ✓ seerr) */
    .chip-container {
      display: flex;
      flex-wrap: wrap;
      gap: 4px;
      margin-top: 4px;
    }

    .chip {
      display: inline-flex;
      align-items: center;
      gap: 3px;
      padding: 2px 6px;
      border-radius: 4px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.08);
      font-size: 0.7rem;
      color: var(--vault-subtext);
    }

    .chip.success {
      color: var(--vault-success);
    }

    /* Empty state */
    .empty-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      text-align: center;
      padding: 20px 16px;
      color: var(--vault-subtext);
      font-size: 0.85rem;
      gap: 8px;
    }

    .empty-state-icon {
      color: var(--vault-standby);
    }
  `,
];
