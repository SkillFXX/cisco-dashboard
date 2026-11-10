<script lang="ts">
	import { cn } from "$lib/utils";
	import { X } from "lucide-svelte";
	import type { Snippet } from "svelte";

	let {
		open = $bindable(false),
		title = "",
		description = "",
		class: className = "",
		children
	}: {
		open: boolean;
		title?: string;
		description?: string;
		class?: string;
		children?: Snippet;
	} = $props();

	function close() {
		open = false;
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === "Escape") {
			close();
		}
	}
</script>

<svelte:window onkeydown={handleKeydown} />

{#if open}
	<!-- Backdrop -->
	<div
		class="fixed inset-0 z-50 bg-black/70 backdrop-blur-xs transition-opacity animate-in fade-in duration-200"
		onclick={close}
		role="presentation"
	></div>

	<!-- Dialog modal -->
	<div class="fixed inset-0 z-50 flex items-center justify-center p-4">
		<div
			class={cn(
				"relative w-full max-w-lg rounded-xl border border-app-border bg-app-card p-6 text-fg shadow-2xl animate-in zoom-in-95 duration-200",
				className
			)}
			role="dialog"
			aria-modal="true"
		>
			<button
				onclick={close}
				class="absolute right-4 top-4 rounded-lg p-1 text-muted hover:bg-app-raised hover:text-fg transition-colors cursor-pointer"
				aria-label="Fermer"
			>
				<X class="w-5 h-5" />
			</button>

			{#if title}
				<div class="mb-5">
					<h3 class="text-lg font-semibold tracking-tight text-fg">{title}</h3>
					{#if description}
						<p class="text-sm text-muted mt-1">{description}</p>
					{/if}
				</div>
			{/if}

			{#if children}
				{@render children()}
			{/if}
		</div>
	</div>
{/if}

