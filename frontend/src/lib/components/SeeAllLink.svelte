<script lang="ts">
	import { ArrowUpRight } from "lucide-svelte";

	let { onclick, label = "Voir tout" }: { onclick: () => void; label?: string } = $props();
</script>

<button
	type="button"
	{onclick}
	class="flex items-center gap-1 text-xs font-medium text-muted hover:text-fg transition-colors cursor-pointer"
>
	{label}
	<ArrowUpRight class="w-3 h-3" />
</button>
