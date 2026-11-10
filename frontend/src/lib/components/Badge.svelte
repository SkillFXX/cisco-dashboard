<script lang="ts">
	import { cn } from "$lib/utils";
	import type { Snippet } from "svelte";

	type Variant = "default" | "secondary" | "destructive" | "outline" | "success" | "warning" | "cisco" | "cm" | "td" | "tp" | "ds";

	let {
		variant = "default",
		class: className = "",
		children
	}: {
		variant?: Variant;
		class?: string;
		children?: Snippet;
	} = $props();

	const variantClasses: Record<Variant, string> = {
		default: "bg-cyan-600/15 text-cyan-400 font-medium",
		secondary: "bg-app-raised text-muted font-medium",
		destructive: "bg-red-600/15 text-red-400 font-medium",
		outline: "bg-app-raised text-muted font-medium",
		success: "bg-emerald-600/15 text-emerald-400 font-medium",
		warning: "bg-amber-600/15 text-amber-400 font-medium",
		cisco: "bg-cyan-600/15 text-cyan-400 font-medium",
		cm: "bg-c-cm/15 text-c-cm font-medium",
		td: "bg-c-td/15 text-c-td font-medium",
		tp: "bg-c-tp/15 text-c-tp font-medium",
		ds: "bg-c-ds/15 text-c-ds font-semibold"
	};
</script>

<span class={cn("inline-flex items-center rounded-md px-2 py-0.5 text-[11px] font-medium transition-colors", variantClasses[variant], className)}>
	{#if children}
		{@render children()}
	{/if}
</span>
