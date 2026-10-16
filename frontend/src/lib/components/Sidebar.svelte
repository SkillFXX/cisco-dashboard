<script lang="ts">
	import { auth } from "$lib/stores/auth.svelte";
	import {
		LayoutDashboard,
		Calendar,
		FileText,
		GraduationCap,
		Clock,
		Settings,
		LogOut
	} from "lucide-svelte";

	let {
		activeTab = $bindable("dashboard"),
		servicesStatus = { scodoc: true, moodle: true, ical: true }
	}: {
		activeTab: string;
		servicesStatus?: { scodoc?: boolean; moodle?: boolean; ical?: boolean };
	} = $props();

	const navItems = [
		{ id: "dashboard", label: "Tableau de bord", icon: LayoutDashboard },
		{ id: "timetable", label: "Emploi du temps", icon: Calendar },
		{ id: "grades", label: "Notes & UEs", icon: FileText },
		{ id: "tasks", label: "Devoirs & DS", icon: GraduationCap },
		{ id: "absences", label: "Absences", icon: Clock },
		{ id: "settings", label: "Paramètres", icon: Settings }
	];
</script>

<aside class="w-60 shrink-0 bg-app-bg border-r border-app-border flex flex-col justify-between min-h-screen select-none sticky top-0 h-screen z-20">
	<div>
		<!-- En-tete Logo Cisco avec icon.png -->
		<div class="px-5 py-6 flex items-center gap-3">
			<img src="/icon.png" alt="Cisco" class="w-8 h-8 rounded-lg object-contain shadow-sm" />
			<div class="flex items-center gap-2">
				<span class="font-extrabold text-base tracking-tight text-white font-sans">Cisco</span>
				<span class="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-zinc-800 text-zinc-300">
					BUT R&T
				</span>
			</div>
		</div>

		<!-- Liens de navigation avec fond blanc transparent sans bordure sur l'onglet actif -->
		<nav class="px-3 py-1 space-y-1">
			{#each navItems as item}
				{@const Icon = item.icon}
				{@const isActive = activeTab === item.id}
				<button
					onclick={() => (activeTab = item.id)}
					class="w-full flex items-center justify-between px-3.5 py-2.5 rounded-lg text-xs font-medium transition-all group cursor-pointer {isActive
						? 'bg-white/[0.08] text-white'
						: 'text-zinc-400 hover:text-white hover:bg-white/[0.03]'}"
				>
					<div class="flex items-center gap-3">
						<Icon class="w-4 h-4 transition-colors {isActive ? 'text-white' : 'text-zinc-400 group-hover:text-zinc-200'}" />
						<span>{item.label}</span>
					</div>

					{#if isActive}
						<div class="w-1.5 h-1.5 rounded-full bg-white"></div>
					{/if}
				</button>
			{/each}
		</nav>
	</div>

	<!-- Section basse : Synchronisation des services & Deconnexion -->
	<div class="p-4 space-y-3">
		<div class="p-3 rounded-lg bg-app-card border border-app-border text-xs space-y-2">
			<div class="font-semibold text-zinc-300 text-[11px] tracking-wide">
				Synchronisation des services
			</div>

			<div class="space-y-1.5 text-[11px]">
				<div class="flex items-center justify-between">
					<span class="text-zinc-400">ScoDoc & ADE</span>
					<span class="px-2.5 py-0.5 rounded-full font-medium text-[10px] {servicesStatus?.scodoc ? 'bg-emerald-600 text-white' : 'bg-zinc-800 text-zinc-400'}">
						{servicesStatus?.scodoc ? "Connecté" : "Déconnecté"}
					</span>
				</div>
				<div class="flex items-center justify-between">
					<span class="text-zinc-400">Moodle</span>
					<span class="px-2.5 py-0.5 rounded-full font-medium text-[10px] {servicesStatus?.moodle ? 'bg-emerald-600 text-white' : 'bg-zinc-800 text-zinc-400'}">
						{servicesStatus?.moodle ? "Connecté" : "Déconnecté"}
					</span>
				</div>
			</div>
		</div>

		{#if auth.user}
			<button
				onclick={() => auth.logout()}
				class="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-lg text-xs font-medium text-zinc-400 hover:text-red-400 hover:bg-white/[0.04] transition-colors cursor-pointer"
			>
				<LogOut class="w-3.5 h-3.5" />
				<span>Déconnexion</span>
			</button>
		{/if}
	</div>
</aside>
