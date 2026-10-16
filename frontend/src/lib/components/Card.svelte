<script lang="ts">
	import { cn } from "$lib/utils";
	import type { Snippet } from "svelte";

	let {
		class: className = "",
		children,
		onclick,
		...rest
	}: {
		class?: string;
		children?: Snippet;
		onclick?: (e: MouseEvent) => void;
		[key: string]: any;
	} = $props();
</script>

<!-- svelte-ignore a11y_click_events_have_key_events -->
<!-- svelte-ignore a11y_no_static_element_interactions -->
<div {onclick} {...rest} class={cn("rounded-xl border border-app-border bg-app-card p-5 shadow-xs transition-all", className)}>
	{#if children}
		{@render children()}
	{/if}
</div>
