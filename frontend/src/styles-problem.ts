import { css } from "lit";

export const problemCardStyles = css`
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

  .title .icon {
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

  .problems {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .problem {
    display: grid;
    grid-template-columns: auto 1fr;
    column-gap: 12px;
    row-gap: 2px;
    align-items: start;
    padding: 10px 12px;
    border-radius: 10px;
    background: var(--card-background-color, rgba(0, 0, 0, 0.04));
    box-shadow: inset 0 0 0 1px var(--divider-color, rgba(0, 0, 0, 0.08));
    border-left: 4px solid var(--problem-color, #9e9e9e);
  }

  .severity {
    grid-row: 1;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 2px 8px;
    border-radius: 999px;
    color: white;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    background: var(--problem-color, #9e9e9e);
    white-space: nowrap;
  }

  .message {
    grid-row: 1;
    grid-column: 2;
    font-size: 0.95rem;
    font-weight: 600;
    line-height: 1.3;
  }

  .details {
    grid-row: 2;
    grid-column: 2;
    display: flex;
    flex-wrap: wrap;
    gap: 4px 12px;
    font-size: 0.8rem;
    color: var(--secondary-text-color, #757575);
  }

  .details .sep {
    opacity: 0.6;
  }

  .empty {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 12px;
    border-radius: 10px;
    background: var(--secondary-background-color, rgba(67, 160, 71, 0.08));
    color: var(--success-color, #43a047);
    font-weight: 500;
  }

  .unavailable {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 12px;
    border-radius: 10px;
    background: var(--secondary-background-color, rgba(0, 0, 0, 0.03));
    color: var(--secondary-text-color, #757575);
    font-style: italic;
  }

  .more {
    font-size: 0.8rem;
    color: var(--secondary-text-color, #757575);
    text-align: center;
    padding: 4px 0 0;
  }

  @media (max-width: 360px) {
    ha-card {
      padding: 12px;
    }

    .title {
      font-size: 1rem;
    }

    .problem {
      grid-template-columns: 1fr;
    }

    .message,
    .details {
      grid-column: 1;
    }
  }
`;
