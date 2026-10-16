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
		{ id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
		{ id: "timetable", label: "Schedule (EDT)", icon: Calendar },
		{ id: "grades", label: "Grades (Scodoc)", icon: FileText },
		{ id: "tasks", label: "Moodle Tasks", icon: GraduationCap },
		{ id: "settings", label: "Settings", icon: Settings }
	];
</script>

<aside class="w-56 shrink-0 bg-[#0B0E14] border-r border-[#1B212D] flex flex-col justify-between min-h-screen select-none sticky top-0 h-screen z-20">
	<div>
		<!-- Brand Logo -->
		<div class="px-5 py-6 flex items-center gap-3">
			<div class="w-8 h-8 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 shadow-[0_0_12px_rgba(6,182,212,0.15)]">
				<!-- Soundwave / signal bars icon matching mockup -->
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
				<span class="font-extrabold text-lg tracking-tight text-white font-sans">Cisco</span>
			</div>
		</div>

		<!-- Nav Links -->
		<nav class="px-2.5 py-1 space-y-1">
			{#each navItems as item}
				{@const Icon = item.icon}
				{@const isActive = activeTab === item.id}
				<button
					onclick={() => (activeTab = item.id)}
					class="w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all group cursor-pointer {isActive
						? 'bg-[#141924] text-white shadow-sm border border-[#202738]'
						: 'text-zinc-400 hover:text-zinc-200 hover:bg-[#121620]'}"
				>
					<div class="flex items-center gap-3">
						<Icon class="w-4 h-4 transition-colors {isActive ? 'text-cyan-400' : 'text-zinc-500 group-hover:text-zinc-300'}" />
						<span>{item.label}</span>
					</div>

					{#if isActive}
						<!-- Glowing cyan indicator dot matching mockup -->
						<div class="w-1.5 h-1.5 rounded-full bg-cyan-400 shadow-[0_0_8px_#22d3ee]"></div>
					{/if}
				</button>
			{/each}
		</nav>
	</div>

	<!-- Bottom Section: API Sync Card & Logout -->
	<div class="p-3.5 space-y-3">
		<!-- API & iCal Sync Box matching mockup -->
		<div class="p-3 rounded-xl bg-[#111622] border border-[#1C2230] text-xs space-y-2">
			<div class="font-bold text-zinc-300 text-[11px] tracking-wide">API & iCal Sync</div>

			<div class="space-y-1.5 text-[11px]">
				<div class="flex items-center justify-between">
					<span class="text-zinc-400">Status</span>
					<span class="px-2 py-0.5 rounded-full font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-[10px]">
						Connected
					</span>
				</div>
				<div class="flex items-center justify-between">
					<span class="text-zinc-400">Badges</span>
					<span class="px-2 py-0.5 rounded-full font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-[10px]">
						Connected
					</span>
				</div>
			</div>
		</div>

		<!-- Logout button -->
		{#if auth.user}
			<button
				onclick={() => auth.logout()}
				class="w-full flex items-center justify-center gap-2 py-1.5 px-3 rounded-lg text-xs font-medium text-zinc-400 hover:text-red-400 hover:bg-red-500/10 transition-colors cursor-pointer"
			>
				<LogOut class="w-3.5 h-3.5" />
				<span>Déconnexion</span>
			</button>
		{/if}
	</div>
</aside>
