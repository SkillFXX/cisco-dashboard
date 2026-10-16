<script lang="ts">
	import { auth } from "$lib/stores/auth.svelte";
	import {
		LayoutDashboard,
		Calendar,
		FileText,
		GraduationCap,
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
		{ id: "settings", label: "Paramètres", icon: Settings }
	];
</script>

<aside class="w-60 shrink-0 bg-[#080A0F] border-r border-[#151B26] flex flex-col justify-between min-h-screen select-none sticky top-0 h-screen z-20">
	<div>
		<!-- En-tete Logo Cisco -->
		<div class="px-5 py-6 flex items-center gap-3">
			<div class="w-8 h-8 rounded-lg bg-cyan-950/60 border border-cyan-800/40 flex items-center justify-center text-cyan-400">
				<!-- Icone ondes signal -->
				<svg class="w-4 h-4 text-cyan-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
					<path d="M2 10v4" />
					<path d="M6 6v12" />
					<path d="M10 2v20" />
					<path d="M14 6v12" />
					<path d="M18 10v4" />
					<path d="M22 11v2" />
				</svg>
			</div>
			<div class="flex items-center gap-2">
				<span class="font-extrabold text-base tracking-tight text-zinc-100 font-sans">Cisco</span>
				<span class="text-[10px] font-mono font-medium px-1.5 py-0.5 rounded bg-zinc-900 text-zinc-400 border border-zinc-800">
					BUT R&T
				</span>
			</div>
		</div>

		<!-- Liens de navigation -->
		<nav class="px-3 py-1 space-y-1">
			{#each navItems as item}
				{@const Icon = item.icon}
				{@const isActive = activeTab === item.id}
				<button
					onclick={() => (activeTab = item.id)}
					class="w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-medium transition-all group cursor-pointer {isActive
						? 'bg-[#111724] text-white border border-[#1A253A]'
						: 'text-zinc-400 hover:text-zinc-200 hover:bg-[#0E131E]'}"
				>
					<div class="flex items-center gap-3">
						<Icon class="w-4 h-4 transition-colors {isActive ? 'text-cyan-400' : 'text-zinc-500 group-hover:text-zinc-300'}" />
						<span>{item.label}</span>
					</div>

					{#if isActive}
						<div class="w-1.5 h-1.5 rounded-full bg-cyan-400 shadow-[0_0_8px_#22d3ee]"></div>
					{/if}
				</button>
			{/each}
		</nav>
	</div>

	<!-- Section basse : Synchronisation des services & Deconnexion -->
	<div class="p-4 space-y-3">
		<div class="p-3 rounded-xl bg-[#0D111A] border border-[#151B26] text-xs space-y-2">
			<div class="font-semibold text-zinc-300 text-[11px] tracking-wide">
				Synchronisation des services
			</div>

			<div class="space-y-1.5 text-[11px]">
				<div class="flex items-center justify-between">
					<span class="text-zinc-400">ScoDoc & ADE</span>
					<span class="px-2 py-0.5 rounded-full font-medium text-[10px] {servicesStatus?.scodoc ? 'bg-emerald-950/60 text-emerald-400 border border-emerald-800/40' : 'bg-zinc-900 text-zinc-500'}">
						{servicesStatus?.scodoc ? "Connecté" : "Déconnecté"}
					</span>
				</div>
				<div class="flex items-center justify-between">
					<span class="text-zinc-400">Moodle</span>
					<span class="px-2 py-0.5 rounded-full font-medium text-[10px] {servicesStatus?.moodle ? 'bg-emerald-950/60 text-emerald-400 border border-emerald-800/40' : 'bg-zinc-900 text-zinc-500'}">
						{servicesStatus?.moodle ? "Connecté" : "Déconnecté"}
					</span>
				</div>
			</div>
		</div>

		{#if auth.user}
			<button
				onclick={() => auth.logout()}
				class="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-lg text-xs font-medium text-zinc-400 hover:text-red-400 hover:bg-red-950/30 transition-colors cursor-pointer"
			>
				<LogOut class="w-3.5 h-3.5" />
				<span>Déconnexion</span>
			</button>
		{/if}
	</div>
</aside>
