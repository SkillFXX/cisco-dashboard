const API_BASE = "http://localhost:8000/api";

function getAuthHeader(): Record<string, string> {
	if (typeof window === "undefined") return {};
	const token = localStorage.getItem("cisco_token");
	if (token) {
		return { Authorization: `Bearer ${token}` };
	}
	return {};
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
	const headers = {
		"Content-Type": "application/json",
		...getAuthHeader(),
		...(options.headers || {})
	};

	const res = await fetch(`${API_BASE}${endpoint}`, {
		...options,
		headers
	});

	if (res.status === 401) {
		if (typeof window !== "undefined") {
			localStorage.removeItem("cisco_token");
			localStorage.removeItem("cisco_user");
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
	async login(username: string, password: string) {
		const data = await request<{ access_token: string; user: any }>("/auth/login", {
			method: "POST",
			body: JSON.stringify({ username, password })
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

	async getMe() {
		return await request<any>("/auth/me");
	},

	logout() {
		localStorage.removeItem("cisco_token");
		localStorage.removeItem("cisco_user");
	},

	// Dashboard
	async getDashboardOverview() {
		return await request<any>("/dashboard/overview");
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

	// Moodle
	async getMoodleAssignments() {
		return await request<any>("/moodle/assignments");
	},

	async getMoodleCourses() {
		return await request<any>("/moodle/courses");
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
	}
};

