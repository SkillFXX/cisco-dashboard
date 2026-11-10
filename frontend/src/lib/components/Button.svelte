<script lang="ts">
	import { cn } from "$lib/utils";
	import type { Snippet } from "svelte";

	type Variant = "default" | "secondary" | "destructive" | "outline" | "ghost" | "link" | "cisco";
	type Size = "default" | "sm" | "lg" | "icon";

	let {
		variant = "default",
		size = "default",
		type = "button",
		disabled = false,
		class: className = "",
		onclick,
		children
	}: {
		variant?: Variant;
		size?: Size;
		type?: "button" | "submit" | "reset";
		disabled?: boolean;
		class?: string;
		onclick?: (e: MouseEvent) => void;
		children?: Snippet;
	} = $props();

	const variantClasses: Record<Variant, string> = {
		default: "bg-cyan-600 text-white font-semibold hover:bg-cyan-500 shadow-xs active:scale-[0.98]",
		secondary: "bg-app-raised text-fg hover:bg-app-raised2/80 border border-app-border active:scale-[0.98]",
		destructive: "bg-red-600 text-white hover:bg-red-500 shadow-sm active:scale-[0.98]",
		outline: "border border-app-border bg-transparent hover:bg-app-raised/80 text-fg active:scale-[0.98]",
		ghost: "hover:bg-app-raised/80 text-muted hover:text-fg",
		link: "text-cyan-400 underline-offset-4 hover:underline p-0 h-auto",
		cisco: "bg-cyan-600 text-white font-semibold hover:bg-cyan-500 shadow-xs active:scale-[0.98]"
	};

	const sizeClasses: Record<Size, string> = {
		default: "h-9 px-4 py-2 text-xs",
		sm: "h-8 px-3 text-xs",
		lg: "h-10 px-5 text-sm",
		icon: "h-9 w-9 p-0 flex items-center justify-center"
	};
</script>

<button
	{type}
	{disabled}
	{onclick}
	class={cn(
		"inline-flex items-center justify-center gap-2 rounded-lg font-medium transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-app-bg disabled:pointer-events-none disabled:opacity-50 cursor-pointer",
		variantClasses[variant],
		sizeClasses[size],
		className
	)}
>
	{#if children}
		{@render children()}
	{/if}
</button>

