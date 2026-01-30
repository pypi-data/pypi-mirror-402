from pythreejs import ParametricGeometry, Mesh, BufferGeometryLoader

f = '''
function f(origu, origv) {
  var u = 2*Math.PI*origu
  var v = 2*Math.PI*origv

  var x = Math.sin(u)
  var y = Math.cos(v)
  var z = Math.cos(u+v)

  return new THREE.Vector3(x,y,z)
}
'''
surf_g = ParametricGeometry(func=f)

loader = BufferGeometryLoader()

loader.load('pressure.json')
