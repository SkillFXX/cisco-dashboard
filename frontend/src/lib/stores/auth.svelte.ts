import { api } from "../api";

export interface UserProfile {
	id: number;
	email: string;
	username?: string;
	full_name?: string;
	photo_base64?: string | null;
	has_scodoc?: boolean;
	has_moodle?: boolean;
	has_ical?: boolean;
}

class AuthStore {
	user = $state<UserProfile | null>(null);
	token = $state<string | null>(null);
	isLoading = $state<boolean>(true);
	isAuthenticated = $derived(!!this.token && !!this.user);

	constructor() {
		if (typeof window !== "undefined") {
			this.token = localStorage.getItem("cisco_token");
			const savedUser = localStorage.getItem("cisco_user");
			if (savedUser) {
				try {
					this.user = JSON.parse(savedUser);
				} catch {
					this.user = null;
				}
			}
			this.isLoading = false;
		}
	}

	async init() {
		if (typeof window === "undefined") return;
		this.token = localStorage.getItem("cisco_token");
		if (this.token) {
			try {
				const userMe = await api.getMe();
				this.user = userMe;
				localStorage.setItem("cisco_user", JSON.stringify(userMe));
			} catch (e) {
				console.warn("Session check failed", e);
				this.logout();
			}
		}
		this.isLoading = false;
	}

	async login(email: string, pwd: string) {
		const res = await api.login(email, pwd);
		this.token = res.access_token;
		this.user = res.user;
		// fetch fresh user details
		try {
			const me = await api.getMe();
			this.user = me;
			localStorage.setItem("cisco_user", JSON.stringify(me));
		} catch {
			// keep user from login response
		}
		return res;
	}

	async register(payload: any) {
		const res = await api.register(payload);
		this.token = res.access_token;
		this.user = res.user;
		try {
			const me = await api.getMe();
			this.user = me;
			localStorage.setItem("cisco_user", JSON.stringify(me));
		} catch {
			// keep user from register response
		}
		return res;
	}

	async updateProfile(profile: any) {
		const updated = await api.updateProfile(profile);
		this.user = updated;
		if (typeof window !== "undefined") {
			localStorage.setItem("cisco_user", JSON.stringify(updated));
		}
		return updated;
	}

	logout() {
		api.logout();
		this.token = null;
		this.user = null;
	}
}

export const auth = new AuthStore();

