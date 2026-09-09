import { useState } from "react";
import { useAppStore } from "../store/useAppStore";
import { login, register } from "../lib/api";

export default function AuthWidget() {
  const { authToken, userEmail } = useAppStore();
  const setAuth = useAppStore((s) => s.setAuth);
  const [open, setOpen] = useState(false);
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (authToken) {
    return (
      <div className="ml-auto flex items-center gap-3 text-sm">
        <span className="text-slate-400">{userEmail}</span>
        <button
          onClick={() => setAuth(null, null)}
          className="text-slate-400 hover:text-slate-200 border border-slate-700 rounded px-2.5 py-1"
        >
          Log out
        </button>
      </div>
    );
  }

  const submit = async () => {
    setBusy(true);
    setError(null);
    try {
      if (mode === "register") {
        await register(email, password);
      }
      const { access_token } = await login(email, password);
      setAuth(access_token, email);
      setOpen(false);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="ml-auto relative">
      <button
        onClick={() => setOpen((v) => !v)}
        className="text-sm text-slate-300 hover:text-white border border-slate-700 rounded px-3 py-1"
      >
        Log in / Register
      </button>
      {open && (
        <div className="absolute right-0 top-9 w-64 bg-slate-900 border border-slate-700 rounded-lg p-3 shadow-xl z-10 text-sm">
          <div className="flex gap-2 mb-2 text-xs">
            <button
              onClick={() => setMode("login")}
              className={`flex-1 py-1 rounded ${mode === "login" ? "bg-cyan-600 text-white" : "bg-slate-800 text-slate-400"}`}
            >
              Log in
            </button>
            <button
              onClick={() => setMode("register")}
              className={`flex-1 py-1 rounded ${mode === "register" ? "bg-cyan-600 text-white" : "bg-slate-800 text-slate-400"}`}
            >
              Register
            </button>
          </div>
          <input
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 rounded px-2 py-1 mb-2 text-slate-200"
          />
          <input
            placeholder="Password (8+ chars)"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 rounded px-2 py-1 mb-2 text-slate-200"
          />
          {error && <p className="text-red-400 text-xs mb-2">{error}</p>}
          <button
            onClick={submit}
            disabled={busy || !email || password.length < 8}
            className="w-full bg-cyan-600 hover:bg-cyan-500 disabled:bg-slate-700 disabled:text-slate-500 text-white rounded py-1.5 font-medium"
          >
            {busy ? "…" : mode === "login" ? "Log in" : "Create account"}
          </button>
          <p className="text-slate-500 text-xs mt-2">
            Saving projects/analyses is optional — everything else works without an account.
          </p>
        </div>
      )}
    </div>
  );
}
