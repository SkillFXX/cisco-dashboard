export type ThemeMode = "auto" | "light" | "dark";

const STORAGE_KEY = "cisco_theme";
const THEME_COLORS = { light: "#f4f5f8", dark: "#0b0c11" };

function systemPrefersLight(): boolean {
	return typeof window !== "undefined" && window.matchMedia("(prefers-color-scheme: light)").matches;
}

function apply(mode: ThemeMode) {
	if (typeof document === "undefined") return;
	const root = document.documentElement;
	if (mode === "auto") root.removeAttribute("data-theme");
	else root.setAttribute("data-theme", mode);
	const resolved = mode === "auto" ? (systemPrefersLight() ? "light" : "dark") : mode;
	document.querySelector('meta[name="theme-color"]')?.setAttribute("content", THEME_COLORS[resolved]);
}

class ThemeStore {
	mode = $state<ThemeMode>("auto");

	init() {
		try {
			const saved = localStorage.getItem(STORAGE_KEY);
			if (saved === "light" || saved === "dark") this.mode = saved;
		} catch {
			// stockage indisponible : mode automatique
		}
		apply(this.mode);
		// En mode automatique, suit le système en direct
		window.matchMedia("(prefers-color-scheme: light)").addEventListener("change", () => {
			if (this.mode === "auto") apply("auto");
		});
	}

	set(mode: ThemeMode) {
		this.mode = mode;
		try {
			if (mode === "auto") localStorage.removeItem(STORAGE_KEY);
			else localStorage.setItem(STORAGE_KEY, mode);
		} catch {
			// ignore
		}
		apply(mode);
	}
}

export const theme = new ThemeStore();
