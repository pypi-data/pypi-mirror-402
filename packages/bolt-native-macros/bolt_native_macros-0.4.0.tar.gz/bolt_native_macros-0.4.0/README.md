# Bolt Native Macros
> Lets you use macros naturally within your bolt code

## Configuration
1. Setup `beet.yml`/`beet.json`
```yml
pipeline:
 - mecha

require:
 - bolt
 - bolt_expressions    # Optional but has compatibility
 - bolt_native_macros
```
2. Start using macros
```mcfunction
if score @s id matches $(id) say me
```
```mcfunction
$execute if score @s id matches $(id) run say me
```