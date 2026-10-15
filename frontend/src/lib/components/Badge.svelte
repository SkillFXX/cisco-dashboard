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
		default: "bg-primary text-primary-foreground hover:bg-primary/80",
		secondary: "bg-zinc-800 text-zinc-100 border border-zinc-700/60",
		destructive: "bg-red-500/15 text-red-400 border border-red-500/30",
		outline: "text-zinc-300 border border-zinc-700",
		success: "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30",
		warning: "bg-amber-500/15 text-amber-400 border border-amber-500/30",
		cisco: "bg-cyan-500/15 text-cyan-400 border border-cyan-500/30",
		cm: "bg-purple-500/15 text-purple-400 border border-purple-500/30",
		td: "bg-blue-500/15 text-blue-400 border border-blue-500/30",
		tp: "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30",
		ds: "bg-rose-500/20 text-rose-300 border border-rose-500/40 font-semibold"
	};
</script>

<span class={cn("inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium transition-colors", variantClasses[variant], className)}>
	{#if children}
		{@render children()}
	{/if}
</span>

