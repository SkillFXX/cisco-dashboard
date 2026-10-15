<script lang="ts">
	import { auth } from "$lib/stores/auth.svelte";
	import Badge from "./Badge.svelte";
	import Button from "./Button.svelte";
	import {
		LayoutDashboard,
		GraduationCap,
		CalendarDays,
		ListTodo,
		Clock,
		Settings,
		PlusCircle,
		LogOut,
		Radio,
		Layers
	} from "lucide-svelte";

	let {
		activeTab = $bindable("dashboard"),
		onOpenAddTask
	}: {
		activeTab: string;
		onOpenAddTask?: () => void;
	} = $props();

	const tabs = [
		{ id: "dashboard", label: "Vue d'ensemble", icon: LayoutDashboard },
		{ id: "grades", label: "Notes & UEs", icon: GraduationCap },
		{ id: "timetable", label: "Emploi du temps", icon: CalendarDays },
		{ id: "tasks", label: "Devoirs & DS", icon: ListTodo },
		{ id: "absences", label: "Absences", icon: Clock },
		{ id: "settings", label: "Services & Paramètres", icon: Settings }
	];
</script>

<header class="sticky top-0 z-40 border-b border-zinc-800 bg-zinc-950/80 backdrop-blur-md">
	<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
		<div class="flex items-center justify-between h-16">
			<!-- Logo Cisco Student -->
			<div class="flex items-center gap-3">
				<div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-600 via-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20 text-white font-black text-xl tracking-wider">
					C
				</div>
				<div>
					<div class="flex items-center gap-2">
						<span class="font-bold text-lg tracking-tight text-white font-mono">CISCO</span>
						<Badge variant="cisco" class="font-mono text-[10px] tracking-wide uppercase px-2 py-0.5">
							BUT R&T
						</Badge>
					</div>
					<p class="text-xs text-zinc-400 font-sans">Panel Étudiant Universitaire</p>
				</div>
			</div>

			<!-- Center navigation links -->
			<nav class="hidden md:flex items-center space-x-1">
				{#each tabs as tab}
					{@const Icon = tab.icon}
					<button
						onclick={() => (activeTab = tab.id)}
						class="flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all cursor-pointer {activeTab === tab.id ? 'bg-cyan-500/10 text-cyan-400 shadow-xs' : 'text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800/60'}"
					>
						<Icon class="w-4 h-4" />
						<span>{tab.label}</span>
					</button>
				{/each}
			</nav>

			<!-- Right side: Add DS Button + Profile + Logout -->
			<div class="flex items-center gap-3">
				{#if onOpenAddTask}
					<Button variant="cisco" size="sm" onclick={onOpenAddTask} class="hidden sm:inline-flex">
						<PlusCircle class="w-4 h-4" />
						<span>Ajouter un DS</span>
					</Button>
				{/if}

				{#if auth.user}
					<div class="flex items-center gap-2 pl-2 border-l border-zinc-800">
						<div class="w-8 h-8 rounded-full bg-zinc-800 border border-zinc-700 flex items-center justify-center text-xs font-semibold text-zinc-200">
							{auth.user.username.slice(0, 2).toUpperCase()}
						</div>
						<div class="hidden lg:block text-left">
							<div class="text-xs font-medium text-zinc-200 leading-none">
								{auth.user.full_name || auth.user.username}
							</div>
							<div class="text-[10px] text-zinc-500 leading-none mt-1">
								{auth.user.email}
							</div>
						</div>
						<button
							onclick={() => auth.logout()}
							class="p-1.5 rounded-lg text-zinc-400 hover:text-red-400 hover:bg-zinc-800/80 transition-colors cursor-pointer ml-1"
							title="Déconnexion"
						>
							<LogOut class="w-4 h-4" />
						</button>
					</div>
				{/if}
			</div>
		</div>

		<!-- Mobile navigation row -->
		<div class="flex md:hidden overflow-x-auto py-2 gap-1 border-t border-zinc-800/60 scrollbar-none">
			{#each tabs as tab}
				{@const Icon = tab.icon}
				<button
					onclick={() => (activeTab = tab.id)}
					class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-colors {activeTab === tab.id ? 'bg-cyan-500/10 text-cyan-400 font-semibold' : 'text-zinc-400 hover:text-zinc-200'}"
				>
					<Icon class="w-3.5 h-3.5" />
					<span>{tab.label}</span>
				</button>
			{/each}
		</div>
	</div>
</header>

