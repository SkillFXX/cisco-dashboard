<script lang="ts">
	import { auth } from "$lib/stores/auth.svelte";
	import { navItems } from "$lib/nav";
	import { MoreHorizontal, LogOut, X } from "lucide-svelte";

	let { activeTab = $bindable("dashboard") }: { activeTab: string } = $props();

	let isMenuOpen = $state(false);

	let available = $derived(navItems.filter((i) => !i.adminOnly || auth.user?.is_admin));
	let primaryItems = $derived(available.filter((i) => i.primary));
	let moreItems = $derived(available.filter((i) => !i.primary));
	let isMoreActive = $derived(moreItems.some((i) => i.id === activeTab));

	function go(id: string) {
		activeTab = id;
		isMenuOpen = false;
	}
</script>

<nav
	class="md:hidden fixed bottom-0 inset-x-0 z-30 bg-app-bg/95 backdrop-blur border-t border-app-border grid grid-cols-5 pb-[env(safe-area-inset-bottom)]"
	aria-label="Navigation principale"
>
	{#each primaryItems as item}
		{@const Icon = item.icon}
		<button
			onclick={() => go(item.id)}
			class="flex flex-col items-center gap-1 py-2.5 text-[10px] font-medium transition-colors cursor-pointer {activeTab === item.id ? 'text-cyan-400' : 'text-subtle'}"
			aria-current={activeTab === item.id ? "page" : undefined}
		>
			<Icon class="w-5 h-5" />
			<span class="truncate max-w-full px-1">{item.label.split(" ")[0]}</span>
		</button>
	{/each}
	<button
		onclick={() => (isMenuOpen = !isMenuOpen)}
		class="flex flex-col items-center gap-1 py-2.5 text-[10px] font-medium transition-colors cursor-pointer {isMoreActive || isMenuOpen ? 'text-cyan-400' : 'text-subtle'}"
		aria-expanded={isMenuOpen}
	>
		<MoreHorizontal class="w-5 h-5" />
		<span>Plus</span>
	</button>
</nav>

{#if isMenuOpen}
	<div class="md:hidden fixed inset-0 z-40">
		<button class="absolute inset-0 bg-black/70" onclick={() => (isMenuOpen = false)} aria-label="Fermer le menu"></button>
		<div class="absolute bottom-0 inset-x-0 rounded-t-2xl bg-app-card border-t border-app-border p-4 pb-[calc(1rem+env(safe-area-inset-bottom))] space-y-1 animate-in slide-in-from-bottom duration-200">
			<div class="flex items-center justify-between pb-2">
				<span class="text-xs font-semibold text-muted">Menu</span>
				<button onclick={() => (isMenuOpen = false)} class="p-1 text-muted cursor-pointer" aria-label="Fermer">
					<X class="w-4 h-4" />
				</button>
			</div>
			{#each moreItems as item}
				{@const Icon = item.icon}
				<button
					onclick={() => go(item.id)}
					class="w-full flex items-center gap-3 px-3.5 py-3 rounded-lg text-sm font-medium cursor-pointer {activeTab === item.id ? 'bg-fg/[0.08] text-fg' : 'text-muted hover:bg-fg/[0.04]'}"
				>
					<Icon class="w-4 h-4" />
					<span>{item.label}</span>
				</button>
			{/each}
			<button
				onclick={() => auth.logout()}
				class="w-full flex items-center gap-3 px-3.5 py-3 rounded-lg text-sm font-medium text-red-400 hover:bg-fg/[0.04] cursor-pointer"
			>
				<LogOut class="w-4 h-4" />
				<span>Déconnexion</span>
			</button>
		</div>
	</div>
{/if}
