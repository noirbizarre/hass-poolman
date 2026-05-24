import { css } from "lit";

export const quickActionsStyles = css`
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
    font-size: 1.05rem;
    font-weight: 600;
  }

  .buttons {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 8px;
  }

  .qa-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    min-height: 48px;
    padding: 10px 12px;
    border: 1px solid var(--divider-color, rgba(0, 0, 0, 0.12));
    border-radius: 12px;
    background: var(--card-background-color, #fff);
    color: var(--primary-text-color, #212121);
    font: inherit;
    font-weight: 500;
    cursor: pointer;
    transition:
      transform 120ms ease,
      background-color 200ms ease,
      border-color 200ms ease,
      color 200ms ease;
  }

  .qa-btn:focus-visible {
    outline: 2px solid var(--primary-color, #03a9f4);
    outline-offset: 2px;
  }

  .qa-btn:hover:not(:disabled) {
    border-color: var(--primary-color, #03a9f4);
  }

  .qa-btn:active:not(:disabled) {
    transform: scale(0.98);
  }

  .qa-btn:disabled {
    cursor: progress;
    opacity: 0.85;
  }

  .qa-btn[data-state="success"] {
    background: var(--success-color, #43a047);
    border-color: var(--success-color, #43a047);
    color: #fff;
    animation: qa-pop 250ms ease;
  }

  .qa-btn[data-state="error"] {
    background: var(--error-color, #d32f2f);
    border-color: var(--error-color, #d32f2f);
    color: #fff;
  }

  .qa-btn[data-state="pending"] {
    color: var(--secondary-text-color, #6c6c6c);
  }

  .qa-icon {
    font-size: 1.15rem;
    line-height: 1;
  }

  .qa-spinner {
    width: 16px;
    height: 16px;
    border-radius: 50%;
    border: 2px solid currentColor;
    border-right-color: transparent;
    animation: qa-spin 800ms linear infinite;
  }

  .qa-error-message {
    grid-column: 1 / -1;
    font-size: 0.85rem;
    color: var(--error-color, #d32f2f);
    background: color-mix(in srgb, var(--error-color, #d32f2f) 12%, transparent);
    padding: 8px 10px;
    border-radius: 8px;
  }

  .qa-notice {
    font-size: 0.85rem;
    color: var(--warning-color, #ffa000);
  }

  /* Dialog overlay (lives inside the shadow root). */
  .qa-dialog-backdrop {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.4);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 16px;
    z-index: 99;
  }

  .qa-dialog {
    background: var(--card-background-color, #fff);
    color: var(--primary-text-color, #212121);
    border-radius: 14px;
    padding: 20px;
    width: min(420px, 100%);
    max-height: 90vh;
    overflow: auto;
    display: flex;
    flex-direction: column;
    gap: 12px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
  }

  .qa-dialog h2 {
    margin: 0;
    font-size: 1.1rem;
  }

  .qa-field {
    display: flex;
    flex-direction: column;
    gap: 4px;
    font-size: 0.9rem;
  }

  .qa-field label {
    color: var(--secondary-text-color, #6c6c6c);
  }

  .qa-field input,
  .qa-field select,
  .qa-field textarea {
    font: inherit;
    color: inherit;
    background: var(--card-background-color, #fff);
    border: 1px solid var(--divider-color, rgba(0, 0, 0, 0.2));
    border-radius: 8px;
    padding: 8px 10px;
    min-height: 40px;
  }

  .qa-field textarea {
    min-height: 72px;
    resize: vertical;
  }

  .qa-dialog-actions {
    display: flex;
    justify-content: flex-end;
    gap: 8px;
    margin-top: 4px;
  }

  .qa-dialog-actions button {
    min-height: 40px;
    padding: 8px 16px;
    border-radius: 8px;
    border: 1px solid var(--divider-color, rgba(0, 0, 0, 0.2));
    background: var(--card-background-color, #fff);
    color: inherit;
    font: inherit;
    font-weight: 500;
    cursor: pointer;
  }

  .qa-dialog-actions button.primary {
    background: var(--primary-color, #03a9f4);
    border-color: var(--primary-color, #03a9f4);
    color: var(--text-primary-color, #fff);
  }

  .qa-dialog-actions button:disabled {
    opacity: 0.6;
    cursor: progress;
  }

  .qa-validation {
    font-size: 0.85rem;
    color: var(--error-color, #d32f2f);
  }

  @keyframes qa-spin {
    to {
      transform: rotate(360deg);
    }
  }

  @keyframes qa-pop {
    0% {
      transform: scale(1);
    }
    40% {
      transform: scale(1.04);
    }
    100% {
      transform: scale(1);
    }
  }

  @media (prefers-reduced-motion: reduce) {
    .qa-btn,
    .qa-btn[data-state="success"],
    .qa-spinner {
      animation: none;
      transition: none;
    }
  }
`;
