<script lang="ts">
	let {
		class: className = "",
		...restProps
	}: {
		class?: string;
		[key: string]: any;
	} = $props();
</script>

<div class="animate-pulse bg-fg/[0.06] rounded-md {className}" {...restProps}></div>

