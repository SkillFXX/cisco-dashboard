<script lang="ts">
	import { auth } from "$lib/stores/auth.svelte";
	import { Plus } from "lucide-svelte";

	let {
		activeTab = "dashboard",
		onOpenAddTask
	}: {
		activeTab: string;
		onOpenAddTask?: () => void;
	} = $props();

	const breadcrumbsMap: Record<string, { category: string; page: string }> = {
		dashboard: { category: "Tableau de bord", page: "Vue d'ensemble" },
		timetable: { category: "Emploi du temps", page: "Semaine" },
		grades: { category: "Notes", page: "Relevé" },
		tasks: { category: "Devoirs", page: "Échéances" },
		absences: { category: "Absences", page: "Bilan" },
		settings: { category: "Paramètres", page: "Services" },
		notifications: { category: "Notifications", page: "Alertes personnalisées" },
		admin: { category: "Administration", page: "Utilisateurs & serveur" }
	};

	let breadcrumb = $derived(breadcrumbsMap[activeTab] || { category: "Tableau de bord", page: "Vue d'ensemble" });

	let userDisplayName = $derived(() => {
		if (!auth.user) return "Étudiant R&T";
		if (auth.user.full_name && auth.user.full_name.trim()) {
			return `${auth.user.full_name.trim()} (RT2)`;
		}
		if (auth.user.email) {
			return `${auth.user.email.split("@")[0]} (RT2)`;
		}
		return "Étudiant R&T";
	});

	let userInitials = $derived(() => {
		if (!auth.user) return "RT";
		const name = (auth.user.full_name || auth.user.email || "RT").trim();
		const parts = name.split(/[\s._@-]+/);
		if (parts.length >= 2 && parts[0] && parts[1]) {
			return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
		}
		return name.slice(0, 2).toUpperCase();
	});
</script>

<header class="h-14 md:h-16 px-4 md:px-6 border-b border-app-border bg-app-bg flex items-center justify-between sticky top-0 z-20">
	<!-- Fil d'Ariane -->
	<div class="flex items-center gap-2 text-xs min-w-0">
		<img src="/icon.png" alt="" class="w-6 h-6 rounded-md object-contain md:hidden shrink-0" />
		<span class="text-zinc-500 font-medium hidden md:inline">{breadcrumb.category}</span>
		<span class="text-zinc-700 hidden md:inline">/</span>
		<span class="text-zinc-200 font-semibold truncate">
			<span class="md:hidden">{breadcrumb.category}</span><span class="hidden md:inline">{breadcrumb.page}</span>
		</span>
	</div>

	<!-- Commandes a droite -->
	<div class="flex items-center gap-2 md:gap-3 shrink-0">
		<!-- Bouton ajout direct de devoir / DS -->
		{#if onOpenAddTask}
			<button
				onclick={onOpenAddTask}
				class="hidden md:flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold transition-all cursor-pointer shadow-xs"
			>
				<Plus class="w-3.5 h-3.5" />
				<span>Nouveau DS / Devoir</span>
			</button>
			<button
				onclick={onOpenAddTask}
				class="md:hidden flex items-center justify-center w-8 h-8 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white cursor-pointer"
				aria-label="Nouveau devoir"
			>
				<Plus class="w-4 h-4" />
			</button>
		{/if}

		<!-- Profil etudiant -->
		<div class="flex items-center gap-2.5 pl-2 border-l border-app-border">
			<div class="text-right hidden sm:block">
				<div class="text-xs font-semibold text-zinc-200 leading-none">
					{userDisplayName()}
				</div>
				<div class="text-[10px] text-zinc-500 leading-none mt-1">
					IUT Béziers
				</div>
			</div>
			{#if auth.user?.photo_base64}
				<img
					src={auth.user.photo_base64.startsWith("data:") ? auth.user.photo_base64 : `data:image/jpeg;base64,${auth.user.photo_base64}`}
					alt={userDisplayName()}
					class="w-8 h-8 rounded-full object-cover border border-app-border shadow-sm"
				/>
			{:else}
				<div class="w-8 h-8 rounded-full bg-app-card border border-app-border flex items-center justify-center text-xs font-bold text-cyan-400">
					{userInitials()}
				</div>
			{/if}
		</div>
	</div>
</header>
