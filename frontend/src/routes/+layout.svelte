<script lang="ts">
	import './layout.css';
	import type { LayoutProps } from './$types';

	let { children }: LayoutProps = $props();
</script>

<svelte:head>
	<title>Cisco Dashboard</title>
	<link rel="icon" type="image/png" href="/icon.png" />
	<link rel="shortcut icon" type="image/png" href="/icon.png" />
</svelte:head>

{@render children()}
