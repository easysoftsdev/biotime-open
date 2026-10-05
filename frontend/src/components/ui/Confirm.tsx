"use client";

import { useState } from "react";
import { Modal } from "./Modal";
import { apiErrorMessage } from "@/lib/utils";
import { toast } from "./Toaster";

interface ConfirmProps {
  open: boolean;
  onClose: () => void;
  title: string;
  message: string;
  confirmLabel?: string;
  danger?: boolean;
  onConfirm: () => Promise<void> | void;
}

export function Confirm({
  open,
  onClose,
  title,
  message,
  confirmLabel = "Confirm",
  danger = false,
  onConfirm,
}: ConfirmProps) {
  const [busy, setBusy] = useState(false);

  const handle = async () => {
    setBusy(true);
    try {
      await onConfirm();
      onClose();
    } catch (err) {
      toast("error", apiErrorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal
      open={open}
      onClose={busy ? () => {} : onClose}
      title={title}
      size="sm"
      footer={
        <>
          <button className="btn-ghost" onClick={onClose} disabled={busy}>
            Cancel
          </button>
          <button
            className={
              danger
                ? "px-4 py-2 rounded-lg text-sm font-medium bg-red-600 hover:bg-red-500 text-white transition-colors disabled:opacity-50"
                : "btn-primary disabled:opacity-50"
            }
            onClick={handle}
            disabled={busy}
          >
            {busy ? "Working…" : confirmLabel}
          </button>
        </>
      }
    >
      <p className="text-sm text-slate-300">{message}</p>
    </Modal>
  );
}
