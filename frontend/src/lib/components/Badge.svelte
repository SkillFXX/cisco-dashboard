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
		default: "bg-cyan-600 text-white font-medium",
		secondary: "bg-zinc-800 text-zinc-100 font-medium",
		destructive: "bg-red-600 text-white font-medium",
		outline: "bg-zinc-800 text-zinc-200 font-medium",
		success: "bg-emerald-600 text-white font-medium",
		warning: "bg-amber-600 text-white font-medium",
		cisco: "bg-cyan-600 text-white font-medium",
		cm: "bg-purple-600 text-white font-medium",
		td: "bg-blue-600 text-white font-medium",
		tp: "bg-emerald-600 text-white font-medium",
		ds: "bg-rose-600 text-white font-semibold"
	};
</script>

<span class={cn("inline-flex items-center rounded-full px-2.5 py-0.5 text-[11px] font-medium transition-colors shadow-xs", variantClasses[variant], className)}>
	{#if children}
		{@render children()}
	{/if}
</span>
