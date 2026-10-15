<script lang="ts">
	import { cn } from "$lib/utils";
	import type { Snippet } from "svelte";

	let {
		class: className = "",
		children
	}: {
		class?: string;
		children?: Snippet;
	} = $props();
</script>

<div class={cn("rounded-xl border border-zinc-800/80 bg-zinc-900/60 p-5 shadow-sm backdrop-blur-sm transition-all hover:border-zinc-700/70", className)}>
	{#if children}
		{@render children()}
	{/if}
</div>

