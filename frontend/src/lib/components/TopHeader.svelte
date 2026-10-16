<script lang="ts">
	import { auth } from "$lib/stores/auth.svelte";
	import { Search, Bell } from "lucide-svelte";

	let {
		activeTab = "dashboard"
	}: {
		activeTab: string;
	} = $props();

	const breadcrumbsMap: Record<string, { category: string; page: string }> = {
		dashboard: { category: "Dashboard", page: "Overview" },
		timetable: { category: "Schedule", page: "EDT (Emploi du temps)" },
		grades: { category: "Grades", page: "ScoDoc & UEs" },
		tasks: { category: "Moodle Tasks", page: "Devoirs & DS" },
		absences: { category: "Absences", page: "Relevé & Justificatifs" },
		settings: { category: "Settings", page: "Comptes & Synchronisation" }
	};

	let breadcrumb = $derived(breadcrumbsMap[activeTab] || { category: "Dashboard", page: "Overview" });

	let userDisplayName = $derived(() => {
		if (!auth.user) return "Alex M. (RT1)";
		if (auth.user.full_name) {
			const parts = auth.user.full_name.trim().split(" ");
			if (parts.length >= 2) {
				return `${parts[0]} ${parts[1][0]}. (RT2)`;
			}
			return `${auth.user.full_name} (RT2)`;
		}
		if (auth.user.username === "etudiant") return "Alex M. (RT1)";
		return `${auth.user.username} (RT2)`;
	});

	let userInitials = $derived(() => {
		if (!auth.user) return "AM";
		const parts = (auth.user.full_name || auth.user.username).trim().split(" ");
		if (parts.length >= 2) {
			return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
		}
		return auth.user.username.slice(0, 2).toUpperCase();
	});
</script>

<header class="h-16 px-6 border-b border-[#1A202C] bg-[#0B0E14] flex items-center justify-between sticky top-0 z-20">
	<!-- Breadcrumb -->
	<div class="flex items-center gap-2 text-xs">
		<span class="text-zinc-400 font-medium">{breadcrumb.category}</span>
		<span class="text-zinc-600">/</span>
		<span class="text-zinc-200 font-semibold">{breadcrumb.page}</span>
	</div>

	<!-- Center/Right controls -->
	<div class="flex items-center gap-3">
		<!-- Search pill input matching mockup -->
		<div class="relative">
			<Search class="w-3.5 h-3.5 text-zinc-500 absolute left-3 top-1/2 -translate-y-1/2" />
			<input
				type="text"
				placeholder="Search"
				class="w-44 sm:w-56 bg-[#121620] border border-[#202636] rounded-xl pl-8 pr-3 py-1.5 text-xs text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-cyan-500/50 transition-colors"
			/>
		</div>

		<!-- Notification Bell with ping dot -->
		<button
			class="relative w-8 h-8 rounded-xl bg-[#121620] border border-[#202636] flex items-center justify-center text-zinc-400 hover:text-white transition-colors cursor-pointer"
			title="Notifications"
		>
			<Bell class="w-3.5 h-3.5" />
			<span class="absolute top-1.5 right-1.5 w-1.5 h-1.5 rounded-full bg-cyan-400 shadow-[0_0_6px_#22d3ee]"></span>
		</button>

		<!-- User Capsule Profile matching mockup -->
		<div class="flex items-center gap-2 pl-2">
			<div class="text-xs font-semibold text-zinc-200 hidden sm:block">
				{userDisplayName()}
			</div>
			<div class="w-8 h-8 rounded-full bg-gradient-to-tr from-cyan-600 to-blue-600 border border-cyan-400/30 flex items-center justify-center text-xs font-bold text-white shadow-sm overflow-hidden">
				{userInitials()}
			</div>
		</div>
	</div>
</header>
