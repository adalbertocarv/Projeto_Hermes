import 'dart:convert';
import 'package:http/http.dart' as http;

class BuscarEnderecoService {
  static Future<List<dynamic>> buscarEndereco(String query) async {
    // Constrói a URI de forma mais segura e legível
    final uri = Uri.https('nominatim.openstreetmap.org', '/search', {
      'q': query,
      'format': 'json',
      'addressdetails': '1',
      'viewbox': '-47.9510,-15.5051,-47.3389,-15.8234',
      'bounded': '1', // Restringe a busca ao viewbox
    });

    final response = await http.get(uri);

    if (response.statusCode == 200) {
      // É uma boa prática verificar se o corpo da resposta não está vazio
      if (response.body.isNotEmpty) {
        return json.decode(response.body);
      }
      return []; // Retorna lista vazia se não houver corpo na resposta
    } else {
      throw Exception('Falha para carregar endereço/referencia: ${response.statusCode}');
    }
  }
}