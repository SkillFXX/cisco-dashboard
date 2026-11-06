<script lang="ts">
	import { onMount } from "svelte";
	import { auth } from "$lib/stores/auth.svelte";
	import { LogOut, PanelLeftClose, PanelLeftOpen } from "lucide-svelte";
	import { navItems } from "$lib/nav";
	import { api } from "$lib/api";

	let {
		activeTab = $bindable("dashboard"),
		refreshKey = 0
	}: {
		activeTab: string;
		refreshKey?: number;
	} = $props();

	type ServiceState = "ok" | "error" | "unconfigured" | "loading";
	type ServiceInfo = { state: ServiceState; message: string | null };
	const SERVICES = [
		{ id: "scodoc", label: "ScoDoc" },
		{ id: "moodle", label: "Moodle" },
		{ id: "ical", label: "Emploi du temps" }
	] as const;
	const STATE_LABEL: Record<ServiceState, string> = { ok: "Connecté", error: "Erreur", unconfigured: "Non configuré", loading: "…" };
	const STATE_BADGE: Record<ServiceState, string> = {
		ok: "bg-emerald-600 text-white",
		error: "bg-red-600/90 text-white",
		unconfigured: "bg-zinc-800 text-zinc-400",
		loading: "bg-zinc-800 text-zinc-500"
	};
	const STATE_DOT: Record<ServiceState, string> = { ok: "bg-emerald-500", error: "bg-red-500", unconfigured: "bg-zinc-600", loading: "bg-zinc-700" };

	let services = $state<Record<string, ServiceInfo>>({
		scodoc: { state: "loading", message: null },
		moodle: { state: "loading", message: null },
		ical: { state: "loading", message: null }
	});

	async function refreshServices() {
		try {
			services = await api.getServicesStatus();
		} catch {
			// on garde le dernier etat connu
		}
	}

	$effect(() => {
		refreshKey;
		refreshServices();
	});

	onMount(() => {
		const timer = setInterval(refreshServices, 5 * 60 * 1000);
		return () => clearInterval(timer);
	});

	function serviceTitle(label: string, info: ServiceInfo) {
		return `${label} : ${STATE_LABEL[info.state].toLowerCase()}${info.state === "error" && info.message ? ` (${info.message})` : ""}`;
	}

	let collapsed = $state(false);
	let visibleItems = $derived(navItems.filter((i) => !i.adminOnly || auth.user?.is_admin));

	onMount(() => {
		try {
			collapsed = localStorage.getItem("cisco_sidebar_collapsed") === "1";
		} catch {
			// stockage indisponible : on garde l'état par défaut
		}
	});

	function toggle() {
		collapsed = !collapsed;
		try {
			localStorage.setItem("cisco_sidebar_collapsed", collapsed ? "1" : "0");
		} catch {
			// ignoré
		}
	}
</script>

<aside
	class="hidden md:flex shrink-0 bg-app-bg border-r border-app-border flex-col justify-between select-none sticky top-0 h-screen self-start z-20 overflow-y-auto overflow-x-hidden transition-[width] duration-200 {collapsed ? 'w-16' : 'w-60'}"
>
	<div>
		<!-- En-tête : logo et bouton de repli -->
		<div class="flex items-center {collapsed ? 'flex-col gap-3 px-2 py-4' : 'justify-between px-5 py-6'}">
			<div class="flex items-center gap-3 min-w-0">
				<img src="/icon.png" alt="Cisco Dashboard" class="w-8 h-8 rounded-lg object-contain shadow-sm shrink-0" />
				{#if !collapsed}
					<div class="flex items-center gap-2 min-w-0">
						<span class="font-extrabold text-base tracking-tight text-white font-sans">Cisco</span>
						<span class="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-zinc-800 text-zinc-300">Dashboard</span>
					</div>
				{/if}
			</div>
			<button
				onclick={toggle}
				class="p-1.5 rounded-lg text-zinc-500 hover:text-white hover:bg-white/[0.06] transition-colors cursor-pointer shrink-0"
				aria-label={collapsed ? "Déplier le menu" : "Replier le menu"}
				title={collapsed ? "Déplier le menu" : "Replier le menu"}
			>
				{#if collapsed}<PanelLeftOpen class="w-4 h-4" />{:else}<PanelLeftClose class="w-4 h-4" />{/if}
			</button>
		</div>

		<nav class="py-1 space-y-1 {collapsed ? 'px-2' : 'px-3'}">
			{#each visibleItems as item}
				{@const Icon = item.icon}
				{@const isActive = activeTab === item.id}
				<button
					onclick={() => (activeTab = item.id)}
					title={collapsed ? item.label : undefined}
					aria-label={item.label}
					aria-current={isActive ? "page" : undefined}
					class="w-full flex items-center rounded-lg text-xs font-medium transition-all group cursor-pointer {collapsed ? 'justify-center py-2.5' : 'justify-between px-3.5 py-2.5'} {isActive
						? 'bg-white/[0.08] text-white'
						: 'text-zinc-400 hover:text-white hover:bg-white/[0.03]'}"
				>
					<div class="flex items-center gap-3">
						<Icon class="w-4 h-4 shrink-0 transition-colors {isActive ? 'text-white' : 'text-zinc-400 group-hover:text-zinc-200'}" />
						{#if !collapsed}<span class="whitespace-nowrap">{item.label}</span>{/if}
					</div>
					{#if isActive && !collapsed}
						<div class="w-1.5 h-1.5 rounded-full bg-white"></div>
					{/if}
				</button>
			{/each}
		</nav>
	</div>

	<!-- Section basse : synchronisation des services et déconnexion -->
	<div class="space-y-3 {collapsed ? 'p-2' : 'p-4'}">
		{#if collapsed}
			<div class="flex flex-col items-center gap-2 py-2">
				{#each SERVICES as svc}
					<span class="w-2 h-2 rounded-full {STATE_DOT[services[svc.id].state]}" title={serviceTitle(svc.label, services[svc.id])}></span>
				{/each}
			</div>
		{:else}
			<div class="p-3 rounded-lg bg-app-card border border-app-border text-xs space-y-2">
				<div class="font-semibold text-zinc-300 text-[11px] tracking-wide">Services connectés</div>
				<div class="space-y-1.5 text-[11px]">
					{#each SERVICES as svc}
						<button
							type="button"
							onclick={() => services[svc.id].state !== "ok" && (activeTab = "settings")}
							title={serviceTitle(svc.label, services[svc.id])}
							class="w-full flex items-center justify-between gap-2 {services[svc.id].state === 'ok' ? 'cursor-default' : 'cursor-pointer'}"
						>
							<span class="text-zinc-400">{svc.label}</span>
							<span class="px-2.5 py-0.5 rounded-full font-medium text-[10px] {STATE_BADGE[services[svc.id].state]}">
								{STATE_LABEL[services[svc.id].state]}
							</span>
						</button>
					{/each}
				</div>
			</div>
		{/if}

		{#if auth.user}
			<button
				onclick={() => auth.logout()}
				title={collapsed ? "Déconnexion" : undefined}
				aria-label="Déconnexion"
				class="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-lg text-xs font-medium text-zinc-400 hover:text-red-400 hover:bg-white/[0.04] transition-colors cursor-pointer"
			>
				<LogOut class="w-3.5 h-3.5" />
				{#if !collapsed}<span>Déconnexion</span>{/if}
			</button>
		{/if}
	</div>
</aside>
