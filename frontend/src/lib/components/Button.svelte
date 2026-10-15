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
		default: "bg-cyan-600 text-white hover:bg-cyan-500 shadow-sm shadow-cyan-900/20 active:scale-[0.98]",
		secondary: "bg-zinc-800 text-zinc-100 hover:bg-zinc-700/80 border border-zinc-700/60 active:scale-[0.98]",
		destructive: "bg-red-600 text-white hover:bg-red-500 shadow-sm active:scale-[0.98]",
		outline: "border border-zinc-700/80 bg-transparent hover:bg-zinc-800/80 text-zinc-200 active:scale-[0.98]",
		ghost: "hover:bg-zinc-800/80 text-zinc-300 hover:text-white",
		link: "text-cyan-400 underline-offset-4 hover:underline p-0 h-auto",
		cisco: "bg-gradient-to-r from-cyan-600 to-blue-600 text-white hover:from-cyan-500 hover:to-blue-500 shadow-md shadow-cyan-600/20 active:scale-[0.98]"
	};

	const sizeClasses: Record<Size, string> = {
		default: "h-9 px-4 py-2 text-sm",
		sm: "h-8 px-3 text-xs",
		lg: "h-11 px-6 text-base",
		icon: "h-9 w-9 p-0 flex items-center justify-center"
	};
</script>

<button
	{type}
	{disabled}
	{onclick}
	class={cn(
		"inline-flex items-center justify-center gap-2 rounded-lg font-medium transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-zinc-950 disabled:pointer-events-none disabled:opacity-50 cursor-pointer",
		variantClasses[variant],
		sizeClasses[size],
		className
	)}
>
	{#if children}
		{@render children()}
	{/if}
</button>

