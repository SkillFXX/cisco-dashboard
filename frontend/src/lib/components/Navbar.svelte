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
		{ id: "dashboard", label: "Tableau de bord", icon: LayoutDashboard },
		{ id: "grades", label: "Notes", icon: GraduationCap },
		{ id: "timetable", label: "Emploi du temps", icon: CalendarDays },
		{ id: "tasks", label: "Devoirs", icon: ListTodo },
		{ id: "absences", label: "Absences", icon: Clock },
		{ id: "settings", label: "Paramètres", icon: Settings }
	];
</script>

<header class="sticky top-0 z-40 border-b border-app-border bg-app-bg/80 backdrop-blur-md">
	<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
		<div class="flex items-center justify-between h-16">
			<!-- Logo Cisco Dashboard -->
			<div class="flex items-center gap-3">
				<img src="/icon.png" alt="Cisco Dashboard" class="w-9 h-9 rounded-lg object-contain shadow-sm" />
				<div>
					<div class="flex items-center gap-2">
						<span class="font-bold text-lg tracking-tight text-fg font-sans">Cisco</span>
						<Badge variant="cisco" class="text-[10px] tracking-wide uppercase px-2 py-0.5">
							Dashboard
						</Badge>
					</div>
				</div>
			</div>

			<!-- Center navigation links -->
			<nav class="hidden md:flex items-center space-x-1">
				{#each tabs as tab}
					{@const Icon = tab.icon}
					<button
						onclick={() => (activeTab = tab.id)}
						class="flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all cursor-pointer {activeTab === tab.id ? 'bg-cyan-500/10 text-cyan-400 shadow-xs' : 'text-muted hover:text-fg hover:bg-app-raised/60'}"
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
					<div class="flex items-center gap-2 pl-2 border-l border-app-border">
						<div class="w-8 h-8 rounded-full bg-app-raised border border-app-border flex items-center justify-center text-xs font-semibold text-fg">
							{(auth.user.full_name || auth.user.email || "ET").slice(0, 2).toUpperCase()}
						</div>
						<div class="hidden lg:block text-left">
							<div class="text-xs font-medium text-fg leading-none">
								{auth.user.full_name || auth.user.email}
							</div>
							<div class="text-[10px] text-subtle leading-none mt-1">
								{auth.user.email}
							</div>
						</div>
						<button
							onclick={() => auth.logout()}
							class="p-1.5 rounded-lg text-muted hover:text-red-400 hover:bg-app-raised/80 transition-colors cursor-pointer ml-1"
							title="Déconnexion"
						>
							<LogOut class="w-4 h-4" />
						</button>
					</div>
				{/if}
			</div>
		</div>

		<!-- Mobile navigation row -->
		<div class="flex md:hidden overflow-x-auto py-2 gap-1 border-t border-app-border scrollbar-none">
			{#each tabs as tab}
				{@const Icon = tab.icon}
				<button
					onclick={() => (activeTab = tab.id)}
					class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-colors {activeTab === tab.id ? 'bg-cyan-500/10 text-cyan-400 font-semibold' : 'text-muted hover:text-fg'}"
				>
					<Icon class="w-3.5 h-3.5" />
					<span>{tab.label}</span>
				</button>
			{/each}
		</div>
	</div>
</header>

