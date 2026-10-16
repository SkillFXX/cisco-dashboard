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

<div class={cn("rounded-xl border border-app-border bg-app-card p-5 shadow-xs transition-all", className)}>
	{#if children}
		{@render children()}
	{/if}
</div>
