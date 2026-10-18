<script lang="ts">
	let {
		class: className = "",
		...restProps
	}: {
		class?: string;
		[key: string]: any;
	} = $props();
</script>

<div class="animate-pulse bg-white/[0.06] rounded-md {className}" {...restProps}></div>

