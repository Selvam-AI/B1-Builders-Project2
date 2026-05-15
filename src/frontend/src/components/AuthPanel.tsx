import { ShieldCheck, UserPlus } from "lucide-react";
import type { AuthSubmitHandler, Mode } from "../types";

type AuthPanelProps = {
  mode: Mode;
  setMode: (mode: Mode) => void;
  submitAuth: AuthSubmitHandler;
  busy: boolean;
};

export function AuthPanel({ mode, setMode, submitAuth, busy }: AuthPanelProps) {
  return (
    <section className="auth-section" aria-label="Authentication">
      <div className="section-heading">
        <p className="eyebrow">Start here</p>
        <h2>{mode === "login" ? "Sign in" : "Create member account"}</h2>
      </div>
      <div className="segmented" role="tablist" aria-label="Auth mode">
        <button className={mode === "login" ? "active" : ""} onClick={() => setMode("login")}>
          Sign in
        </button>
        <button
          className={mode === "register" ? "active" : ""}
          onClick={() => setMode("register")}
        >
          <UserPlus size={16} />
          Register
        </button>
      </div>
      <form className="auth-form" onSubmit={submitAuth}>
        {mode === "register" ? (
          <>
            <label>
              Name
              <input name="name" required minLength={1} placeholder="Member name" />
            </label>
            <label>
              Age
              <input name="age" type="number" min={1} max={120} placeholder="Optional" />
            </label>
          </>
        ) : null}
        <label>
          Email
          <input name="email" type="email" required placeholder="member@example.com" />
        </label>
        <label>
          Password
          <input name="password" type="password" required minLength={6} placeholder="member123" />
        </label>
        <button className="primary-button" type="submit" disabled={busy}>
          <ShieldCheck size={18} />
          {mode === "login" ? "Sign in" : "Create account"}
        </button>
      </form>
    </section>
  );
}
