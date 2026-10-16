<script lang="ts">
	import { auth } from "$lib/stores/auth.svelte";
	import { Search, Bell, Plus } from "lucide-svelte";

	let {
		activeTab = "dashboard",
		onOpenAddTask
	}: {
		activeTab: string;
		onOpenAddTask?: () => void;
	} = $props();

	const breadcrumbsMap: Record<string, { category: string; page: string }> = {
		dashboard: { category: "Tableau de bord", page: "Vue d'ensemble" },
		timetable: { category: "Emploi du temps", page: "Semaine en cours" },
		grades: { category: "Notes & Évaluations", page: "Relevé ScoDoc" },
		tasks: { category: "Devoirs & DS", page: "Échéances" },
		absences: { category: "Absences", page: "Justificatifs" },
		settings: { category: "Paramètres", page: "Services & Comptes" }
	};

	let breadcrumb = $derived(breadcrumbsMap[activeTab] || { category: "Tableau de bord", page: "Vue d'ensemble" });

	let userDisplayName = $derived(() => {
		if (!auth.user) return "Étudiant R&T";
		if (auth.user.full_name) {
			return `${auth.user.full_name} (RT2)`;
		}
		return `${auth.user.username} (RT2)`;
	});

	let userInitials = $derived(() => {
		if (!auth.user) return "RT";
		const parts = (auth.user.full_name || auth.user.username).trim().split(" ");
		if (parts.length >= 2) {
			return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
		}
		return auth.user.username.slice(0, 2).toUpperCase();
	});
</script>

<header class="h-16 px-6 border-b border-[#151B26] bg-[#080A0F] flex items-center justify-between sticky top-0 z-20">
	<!-- Fil d'Ariane -->
	<div class="flex items-center gap-2 text-xs">
		<span class="text-zinc-500 font-medium">{breadcrumb.category}</span>
		<span class="text-zinc-700">/</span>
		<span class="text-zinc-200 font-semibold">{breadcrumb.page}</span>
	</div>

	<!-- Commandes a droite -->
	<div class="flex items-center gap-3">
		<!-- Barre de recherche -->
		<div class="relative hidden sm:block">
			<Search class="w-3.5 h-3.5 text-zinc-500 absolute left-3 top-1/2 -translate-y-1/2" />
			<input
				type="text"
				placeholder="Rechercher..."
				class="w-48 md:w-56 bg-[#0E121B] border border-[#1A2230] rounded-xl pl-8 pr-3 py-1.5 text-xs text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-cyan-500/50 transition-colors"
			/>
		</div>

		<!-- Bouton ajout direct de devoir / DS -->
		{#if onOpenAddTask}
			<button
				onclick={onOpenAddTask}
				class="hidden md:flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-cyan-950/40 hover:bg-cyan-900/40 text-cyan-400 border border-cyan-800/40 text-xs font-semibold transition-all cursor-pointer"
			>
				<Plus class="w-3.5 h-3.5" />
				<span>Nouveau DS / Devoir</span>
			</button>
		{/if}

		<!-- Notifications -->
		<button
			class="relative w-8 h-8 rounded-xl bg-[#0E121B] border border-[#1A2230] flex items-center justify-center text-zinc-400 hover:text-white transition-colors cursor-pointer"
			title="Notifications"
		>
			<Bell class="w-3.5 h-3.5" />
			<span class="absolute top-1.5 right-1.5 w-1.5 h-1.5 rounded-full bg-cyan-400"></span>
		</button>

		<!-- Profil etudiant -->
		<div class="flex items-center gap-2.5 pl-2 border-l border-[#151B26]">
			<div class="text-right hidden sm:block">
				<div class="text-xs font-semibold text-zinc-200 leading-none">
					{userDisplayName()}
				</div>
				<div class="text-[10px] text-zinc-500 leading-none mt-1">
					IUT Béziers
				</div>
			</div>
			<div class="w-8 h-8 rounded-full bg-[#111724] border border-[#1E273A] flex items-center justify-center text-xs font-bold text-cyan-400">
				{userInitials()}
			</div>
		</div>
	</div>
</header>
