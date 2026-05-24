import { css } from "lit";

export const cardStyles = css`
  :host {
    display: block;
  }

  ha-card {
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 12px;
    font-family: var(--primary-font-family, sans-serif);
    color: var(--primary-text-color, #212121);
  }

  .header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
  }

  .title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 1.1rem;
    font-weight: 600;
  }

  .title .pool-icon {
    font-size: 1.3rem;
    line-height: 1;
  }

  .badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 10px;
    border-radius: 999px;
    color: white;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    background: var(--badge-color, #9e9e9e);
  }

  .badge .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.85);
  }

  .metrics {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
    gap: 8px;
  }

  .metric {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 2px;
    padding: 8px 10px;
    border-radius: 10px;
    background: var(--card-background-color, rgba(0, 0, 0, 0.04));
    box-shadow: inset 0 0 0 1px var(--divider-color, rgba(0, 0, 0, 0.08));
  }

  .metric-label {
    font-size: 0.75rem;
    color: var(--secondary-text-color, #757575);
    display: flex;
    align-items: center;
    gap: 4px;
  }

  .metric-value {
    font-size: 1.05rem;
    font-weight: 600;
  }

  .score {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .score-row {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    font-size: 0.85rem;
    color: var(--secondary-text-color, #757575);
  }

  .score-row strong {
    color: var(--primary-text-color, #212121);
    font-size: 1rem;
  }

  .score-bar {
    height: 6px;
    border-radius: 999px;
    background: var(--divider-color, rgba(0, 0, 0, 0.08));
    overflow: hidden;
  }

  .score-bar-fill {
    height: 100%;
    background: var(--success-color, #43a047);
    transition: width 0.3s ease;
  }

  .score-bar-fill.warn {
    background: var(--warning-color, #ff9800);
  }

  .score-bar-fill.bad {
    background: var(--error-color, #e53935);
  }

  .recommendations {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    padding: 8px 12px;
    border-radius: 10px;
    background: var(--secondary-background-color, rgba(0, 0, 0, 0.03));
    cursor: pointer;
    user-select: none;
  }

  .recommendations[disabled] {
    cursor: default;
    opacity: 0.7;
  }

  .recommendations:focus-visible {
    outline: 2px solid var(--primary-color, #03a9f4);
    outline-offset: 2px;
  }

  .recommendations .label {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 0.9rem;
  }

  .recommendations .chevron {
    font-size: 1.1rem;
    color: var(--secondary-text-color, #757575);
  }

  @media (max-width: 360px) {
    ha-card {
      padding: 12px;
    }

    .title {
      font-size: 1rem;
    }
  }
`;
