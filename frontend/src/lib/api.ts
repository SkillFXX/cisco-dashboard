const API_BASE = (typeof window !== "undefined" && (window as any).__API_URL__) || import.meta.env?.VITE_API_URL || "http://localhost:8000/api";

function getAuthHeader(): Record<string, string> {
	if (typeof window === "undefined") return {};
	const token = localStorage.getItem("cisco_token");
	if (token) {
		return { Authorization: `Bearer ${token}` };
	}
	return {};
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
	const headers: Record<string, string> = {
		"Content-Type": "application/json",
		...getAuthHeader(),
		...(options.headers as Record<string, string> | undefined)
	};

	const res = await fetch(`${API_BASE}${endpoint}`, {
		...options,
		headers
	});

	// 401 avec un jeton : session expirée. Sans jeton (ex. login), on laisse remonter le message du serveur.
	if (res.status === 401 && headers.Authorization) {
		if (typeof window !== "undefined") {
			localStorage.removeItem("cisco_token");
			localStorage.removeItem("cisco_user");
			window.dispatchEvent(new Event("cisco:unauthorized"));
		}
		throw new Error("Session expirée ou non autorisée");
	}

	if (!res.ok) {
		let errMsg = "Erreur de communication avec le serveur";
		try {
			const errData = await res.json();
			if (errData.detail) {
				errMsg = typeof errData.detail === "string" ? errData.detail : JSON.stringify(errData.detail);
			}
		} catch {
			// ignore
		}
		throw new Error(errMsg);
	}

	if (res.status === 204) {
		return {} as T;
	}

	return await res.json();
}

export const api = {
	// Auth
	async login(email: string, password: string) {
		const data = await request<{ access_token: string; user: any }>("/auth/login", {
			method: "POST",
			body: JSON.stringify({ email, password })
		});
		localStorage.setItem("cisco_token", data.access_token);
		localStorage.setItem("cisco_user", JSON.stringify(data.user));
		return data;
	},

	async register(payload: any) {
		const data = await request<{ access_token: string; user: any }>("/auth/register", {
			method: "POST",
			body: JSON.stringify(payload)
		});
		localStorage.setItem("cisco_token", data.access_token);
		localStorage.setItem("cisco_user", JSON.stringify(data.user));
		return data;
	},

	async getCapabilities() {
		return await request<{ password_reset: boolean }>("/auth/capabilities");
	},

	async forgotPassword(email: string) {
		return await request<{ message: string }>("/auth/forgot-password", {
			method: "POST",
			body: JSON.stringify({ email })
		});
	},

	async resetPassword(token: string, new_password: string) {
		return await request<{ message: string }>("/auth/reset-password", {
			method: "POST",
			body: JSON.stringify({ token, new_password })
		});
	},

	async getMe() {
		return await request<any>("/auth/me");
	},

	async updateProfile(profile: {
		full_name?: string;
		email?: string;
		current_password?: string;
		new_password?: string;
	}) {
		const data = await request<any>("/auth/profile", {
			method: "PUT",
			body: JSON.stringify(profile)
		});
		localStorage.setItem("cisco_user", JSON.stringify(data));
		return data;
	},

	logout() {
		localStorage.removeItem("cisco_token");
		localStorage.removeItem("cisco_user");
	},

	// Dashboard
	async getDashboardOverview(forceRefresh = false) {
		return await request<any>(`/dashboard/overview?force_refresh=${forceRefresh}`);
	},

	// ScoDoc
	async getScoDocSummary(forceRefresh = false) {
		return await request<any>(`/scodoc/summary?force_refresh=${forceRefresh}`);
	},

	async getGrades(forceRefresh = false) {
		return await request<any>(`/scodoc/grades?force_refresh=${forceRefresh}`);
	},

	async getAbsences(forceRefresh = false) {
		return await request<any>(`/scodoc/absences?force_refresh=${forceRefresh}`);
	},

	async getEvaluationDistribution(
		evalId: number | string,
		params?: { min_promo?: number; moy_promo?: number; max_promo?: number; total_promo?: number }
	) {
		const query = new URLSearchParams();
		if (params?.min_promo !== undefined && params.min_promo !== null) query.set("min_promo", String(params.min_promo));
		if (params?.moy_promo !== undefined && params.moy_promo !== null) query.set("moy_promo", String(params.moy_promo));
		if (params?.max_promo !== undefined && params.max_promo !== null) query.set("max_promo", String(params.max_promo));
		if (params?.total_promo !== undefined && params.total_promo !== null) query.set("total_promo", String(params.total_promo));
		const qs = query.toString() ? `?${query.toString()}` : "";
		return await request<any>(`/scodoc/evaluation/${evalId}/distribution${qs}`);
	},

	// Moodle
	async getMoodleAssignments(forceRefresh = false) {
		return await request<any>(`/moodle/assignments?force_refresh=${forceRefresh}`);
	},

	async getMoodleCourses(forceRefresh = false) {
		return await request<any>(`/moodle/courses?force_refresh=${forceRefresh}`);
	},

	// Timetable (ADE / UM Net iCal)
	async getTimetableWeek(forceRefresh = false) {
		return await request<any>(`/timetable/week?force_refresh=${forceRefresh}`);
	},

	async getTimetableToday(forceRefresh = false) {
		return await request<any>(`/timetable/today?force_refresh=${forceRefresh}`);
	},

	// Tasks & DS
	async getTasks(statusFilter?: string) {
		const query = statusFilter ? `?status_filter=${statusFilter}` : "";
		return await request<any[]>(`/tasks${query}`);
	},

	async getCompletedExternalTasks() {
		return await request<string[]>("/tasks/completed-external");
	},

	async toggleItemStatus(itemId: string, status: "todo" | "done") {
		return await request<any>("/tasks/toggle-status", {
			method: "POST",
			body: JSON.stringify({ item_id: itemId, status })
		});
	},

	async createTask(task: {
		title: string;
		description?: string;
		subject?: string;
		due_date: string;
		event_type: string;
		status?: string;
	}) {
		return await request<any>("/tasks", {
			method: "POST",
			body: JSON.stringify(task)
		});
	},

	async updateTask(id: number, task: Partial<{
		title: string;
		description: string;
		subject: string;
		due_date: string;
		event_type: string;
		status: string;
	}>) {
		return await request<any>(`/tasks/${id}`, {
			method: "PUT",
			body: JSON.stringify(task)
		});
	},

	async deleteTask(id: number) {
		return await request<void>(`/tasks/${id}`, {
			method: "DELETE"
		});
	},

	// Settings & Credentials
	async getSettings() {
		return await request<any>("/settings/services");
	},

	async updateSettings(settings: any) {
		return await request<any>("/settings/services", {
			method: "PUT",
			body: JSON.stringify(settings)
		});
	},

	async verifyService(payload: {
		service: "scodoc" | "moodle" | "ical";
		url?: string;
		username?: string;
		password?: string;
		token?: string;
		save_if_valid?: boolean;
	}) {
		return await request<{
			success: boolean;
			service: string;
			message: string;
			student_name?: string;
			student_pic?: string;
			token?: string;
			details?: any;
		}>("/settings/verify", {
			method: "POST",
			body: JSON.stringify(payload)
		});
	},
	// Évolution moyenne / rang
	async getGradeHistory() {
		return await request<Array<{ day: string; moyenne: number | null; rang: number | null; total_promo: number | null }>>("/scodoc/history");
	},

	// Notifications
	async getNotifications() {
		return await request<any>("/notifications");
	},
	async updateNotificationChannels(webhook_url: string | null) {
		return await request<any>("/notifications/channels", { method: "PUT", body: JSON.stringify({ webhook_url }) });
	},
	async createNotificationRule(rule: any) {
		return await request<any>("/notifications/rules", { method: "POST", body: JSON.stringify(rule) });
	},
	async updateNotificationRule(id: number, rule: any) {
		return await request<any>(`/notifications/rules/${id}`, { method: "PUT", body: JSON.stringify(rule) });
	},
	async deleteNotificationRule(id: number) {
		return await request<any>(`/notifications/rules/${id}`, { method: "DELETE" });
	},
	async testNotificationChannel(channel: "email" | "webhook") {
		return await request<any>("/notifications/test", { method: "POST", body: JSON.stringify({ channel }) });
	},

	// Administration
	async adminListUsers() {
		return await request<any[]>("/admin/users");
	},
	async adminUpdateUser(id: number, payload: { full_name?: string; email?: string }) {
		return await request<any>(`/admin/users/${id}`, { method: "PUT", body: JSON.stringify(payload) });
	},
	async adminSetPassword(id: number, new_password: string) {
		return await request<any>(`/admin/users/${id}/password`, { method: "POST", body: JSON.stringify({ new_password }) });
	},
	async adminDeleteUser(id: number) {
		return await request<any>(`/admin/users/${id}`, { method: "DELETE" });
	},
	async adminGetSmtp() {
		return await request<any>("/admin/smtp");
	},
	async adminUpdateSmtp(payload: any) {
		return await request<any>("/admin/smtp", { method: "PUT", body: JSON.stringify(payload) });
	},
	async adminTestSmtp(to?: string) {
		return await request<any>("/admin/smtp/test", { method: "POST", body: JSON.stringify(to ? { to } : {}) });
	}
};

